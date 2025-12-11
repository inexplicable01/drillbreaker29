# from numpy import int256

from app.MapTools.MappingTools import generateMap

import matplotlib.pyplot as plt

import base64
from io import BytesIO
from app.DBFunc.BriefListingController import brieflistingcontroller
import pandas as pd
from app.GraphTools.plt_plots import *
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.config import RECENTLYSOLD, FOR_SALE, PENDING
import statistics
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from app.DBFunc.AIListingController import ailistingcontroller
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE, PENDING
from datetime import datetime, timedelta, date

# model = load('linear_regression_model.joblib')
def ListAllNeighhourhoodsByCities(neighbourhoods, doz):
    return brieflistingcontroller.ListingsByCities(neighbourhoods, doz)

def _as_date(x):
    if x is None:
        return None
    if isinstance(x, date):
        return x
    if isinstance(x, datetime):
        return x.date()
    # try ISO string
    try:
        return datetime.fromisoformat(str(x)).date()
    except Exception:
        return None

def _sold_date_for(br):
    # Adjust these names if your model uses different fields
    for name in ("sold_date", "solddate", "close_date", "closedate", "soldon", "closing_date"):
        d = getattr(br, name, None)
        d = _as_date(d)
        if d:
            return d
    return None

def _week_start(d: date) -> date:
    # Monday anchor
    return d - timedelta(days=d.weekday())

def StatsModelRun(zone_ids, emailcadencedays, daysofconcernforlistings=7):
    # --- helpers ---
    def _epoch_to_date(val):
        """Accepts seconds or ms epoch (int/float/str). Returns date or None."""
        if val is None:
            return None
        try:
            ts = float(val)
            if ts > 1e12:  # ms → s
                ts /= 1000.0
            return datetime.utcfromtimestamp(ts).date()
        except Exception:
            return None

    def _sold_date_for(br):
        """Use soldtime (epoch) → date."""
        return _epoch_to_date(getattr(br, "soldtime", None))

    def _list_date_for(br):
        """
        Try common fields for the first time a listing went live.
        Adjust names as needed for your model.
        """
        for name in ("listtime", "list_time", "list_date", "listed_date", "listdate", "created_at"):
            val = getattr(br, name, None)
            # allow either epoch or ISO date
            d = _epoch_to_date(val)
            if d:
                return d
            if val:
                try:
                    return datetime.fromisoformat(str(val)).date()
                except Exception:
                    pass
        return None

    def _week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())  # Monday

    # --- aggregates ---
    fastest_days = None
    fast_sales = 0
    under_list = 0
    above_list = 0
    sold_prices = []
    sale_to_list_ratios = []
    list2penddayslist = []

    # Pull enough sold inventory to cover 16 weeks (112d) for time series
    series_window_days = max(daysofconcernforlistings, 112)

    soldhomes_cadence = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD,
                                                                            emailcadencedays).all()
    pending_cadance   = brieflistingcontroller.listingsByZonesandStatus(zone_ids, PENDING, emailcadencedays).all()
    forsale_cadance = brieflistingcontroller.listingsByZonesandStatus(zone_ids, FOR_SALE, emailcadencedays).all()
    forsale_total = brieflistingcontroller.listingsByZonesandStatus(zone_ids, FOR_SALE, 720).all()

# For 16-week history of FOR_SALE *new actives per week*, load a long window
    forsale_16w = brieflistingcontroller.listingsByZonesandStatus(zone_ids, FOR_SALE, 16*7).all()
    pending_16W = brieflistingcontroller.listingsByZonesandStatus(zone_ids, PENDING, 16*7).all()
    soldhomes_16w = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD, 16*7).all()

    brieflisting_cadence = pending_cadance + soldhomes_cadence
    brieflistings16W = pending_16W + soldhomes_16w

    for br in brieflisting_cadence:
        d = getattr(br, "list2penddays", None)
        if d is not None:
            list2penddayslist.append(d)
            if d < 8:
                fast_sales += 1

        lp = getattr(br, "listprice", None)
        sp = getattr(br, "soldprice", None)
        if lp is not None and sp is not None and lp > 0:
            if sp < lp:
                under_list += 1
            else:
                above_list += 1
            sold_prices.append(sp)
            sale_to_list_ratios.append(100.0 * (sp / lp))
    new_listings_cadance=[]
    cutoff = datetime.utcnow().date() - timedelta(days=emailcadencedays)
    for br in brieflisting_cadence+forsale_cadance:
        listtime = _list_date_for(br)
        if listtime and cutoff <= listtime <= datetime.utcnow().date():
            new_listings_cadance.append(br)


    # Populate PENDING counts (bucket by pend date)

    total_with_days = len(list2penddayslist)
    median_days = int(round(statistics.median(list2penddayslist))) if total_with_days else None
    avg_days_on_market = float(round(statistics.mean(list2penddayslist), 2)) if total_with_days else None

    avg_sold_price = int(round(statistics.mean(sold_prices))) if sold_prices else None
    median_sold_price = int(round(statistics.median(sold_prices))) if sold_prices else None

    basis_comp = (under_list + above_list)
    pct_over_ask = round(100.0 * above_list / basis_comp, 1) if basis_comp else 0.0
    sale_to_list_avg_pct = round(statistics.mean(sale_to_list_ratios), 2) if sale_to_list_ratios else None
    pct_under_7d = round(100.0 * fast_sales / total_with_days, 1) if total_with_days else 0.0

    # Proxy for price cuts (kept for compatibility): % sold under list
    pct_price_cuts = round(100.0 * under_list / basis_comp, 1) if basis_comp else 0.0

    if total_with_days:
        fastest_days = int(min(list2penddayslist))

    # --- 16-week windows (oldest→newest) ---
    today = datetime.utcnow().date()
    this_monday = _week_start(today)
    week_starts = [this_monday - timedelta(weeks=i) for i in range(15, -1, -1)]

    # Buckets
    price_buckets = {ws: [] for ws in week_starts}    # sold price by sold week
    dom_buckets   = {ws: [] for ws in week_starts}    # DOM by sold week
    newlisting_buckets= {ws: 0  for ws in week_starts}    # count of NEW for-sale by listing week
    pending_buckets = {ws: 0 for ws in week_starts}


    for br in forsale_16w:
        ld = _list_date_for(br)
        if not ld:
            continue
        if ld < week_starts[0] or ld > (week_starts[-1] + timedelta(days=6)):
            continue
        ws = _week_start(ld)
        if ws in newlisting_buckets:
            newlisting_buckets[ws] += 1

        pd = _epoch_to_date(br.pendday)
        if not pd:
            continue
        if pd < week_starts[0] or pd > (week_starts[-1] + timedelta(days=6)):
            continue
        ws = _week_start(pd)
        if ws in pending_buckets:
            pending_buckets[ws] += 1

    # Populate price & DOM (soldhomes, bucket by sold date)
    for br in brieflistings16W:
        sd = _sold_date_for(br)
        if not sd:
            continue
        if sd < week_starts[0] or sd > (week_starts[-1] + timedelta(days=6)):
            continue
        ws = _week_start(sd)
        if ws in price_buckets:
            sp = getattr(br, "soldprice", None)
            if sp is not None:
                price_buckets[ws].append(sp)
            dom = getattr(br, "list2penddays", None)
            if dom is not None:
                dom_buckets[ws].append(dom)

    # Populate “active listings” history as NEW actives per week (forsale_long, bucket by list date)
    today = datetime.utcnow().date()
    this_monday = _week_start(today)
    week_starts = [this_monday - timedelta(weeks=i) for i in range(15, -1, -1)]

    active_listing_16W = []
    for ws in week_starts:
        we = ws + timedelta(days=6)
        count = 0
        for br in brieflistings16W:
            lt = _epoch_to_date(getattr(br, "listtime", None))
            pd = _epoch_to_date(getattr(br, "pendday", None))
            if lt and lt <= we and (pd is None or pd > ws):
                count += 1
        active_listing_16W.append({"week_start": ws.isoformat(), "active_count": count})

    # Build series
    sold_count_16=[]
    median_price_16w = []
    median_dom_16w = []
    newlistings_16w = []
    pending_16w = []

    for ws in week_starts:
        # price series
        pv = price_buckets.get(ws, [])
        mp = int(round(statistics.median(pv))) if pv else None

        pending_16w.append({
            "week_start": ws.isoformat(),
            "new_pending": int(pending_buckets.get(ws, 0)),
        })

        median_price_16w.append({
            "week_start": ws.isoformat(),
            "median_price": mp,
            "count": len(pv),
        })

        # DOM series
        dv = dom_buckets.get(ws, [])
        md = int(round(statistics.median(dv))) if dv else None
        median_dom_16w.append({
            "week_start": ws.isoformat(),
            "median_dom": md,
            "count": len(dv),
        })

        # active listings (new actives that week)
        newlistings_16w.append({
            "week_start": ws.isoformat(),
            "newlistings": int(newlisting_buckets.get(ws, 0)),
        })

    return {
        # counts / snapshots
        "total_sold": len(soldhomes_cadence),
        "total_pending": len(pending_cadance),
        "new_listings": len(new_listings_cadance),
        "for_sale": len(forsale_total),     # kept for backward compatibility

        # speed / competition
        "fast_sales": fast_sales,
        "fastest_days": fastest_days,
        "median_days": median_days,
        "avg_days_on_market": avg_days_on_market,
        "pct_under_7d": pct_under_7d,
        "sale_to_list_avg_pct": sale_to_list_avg_pct,
        "pct_over_ask": pct_over_ask,

        # prices
        "under_list": under_list,
        "above_list": above_list,
        "avg_sold_price": avg_sold_price,
        "median_sold_price": median_sold_price,
        "pct_price_cuts": pct_price_cuts,  # proxy

        # 16-week histories (oldest→newest)
        "median_price_16w": median_price_16w,       # [{week_start, median_price, count}]
        "median_dom_16w": median_dom_16w,           # [{week_start, median_dom, count}]
        "newlistings_16w": newlistings_16w, # [{week_start, new_actives}]"
        "pending_16w":pending_16w,
        "active_listing_16W":active_listing_16W,

    }

from datetime import datetime, timedelta
def AreaReportModelRun(selected_zones, selectedhometypes,soldlastdays):
    unfiltered_homes = []
    zone_ids=[]
    for zonename in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zonename)
        if wzone:
            zone_ids.append(wzone.id)
            # unfiltered_homes=unfiltered_homes+wzone.brief_listings
            # for brieflisting in wzone.brief_listings:
            #     print(brieflisting.__str__())
    soldhomes = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD, soldlastdays, selectedhometypes).all()
    pendings = brieflistingcontroller.listingsByZonesandStatus(zone_ids, PENDING, soldlastdays, selectedhometypes).all()

    transactshomes = soldhomes+pendings
    housesoldpriceaverage={}
    for brieflisting in transactshomes:
        try:
            # Create dynamic key based on bedrooms and bathrooms
            bed_bath_key = f"{int(brieflisting.bedrooms)}bed{int(brieflisting.bathrooms)}bath"
            # Initialize the dictionary for this key if it doesn't already exist
            if bed_bath_key not in housesoldpriceaverage:
                housesoldpriceaverage[bed_bath_key] = {
                    "count": 0,
                    "totalprice": 0,
                    "houses": []
                }

            # Update the values for the current key
            housesoldpriceaverage[bed_bath_key]["count"] += 1
            housesoldpriceaverage[bed_bath_key]["totalprice"] += brieflisting.price
            housesoldpriceaverage[bed_bath_key]["houses"].append(brieflisting)
        except Exception as e:
            print(f"Error processing brieflisting: {e}")
    # Create a map centered around Ballard, Seattle

    for key, value in housesoldpriceaverage.items():
        value['minprice']=1000000000
        value['maxprice']=0
        if value['count']==0:
            value['aveprice'] = 'NA'
        else:
            value['aveprice']= int(value['totalprice']/value['count'])
        for brieflisting in value["houses"]:
            if brieflisting.price<value['minprice']:
                value['minprice'] = brieflisting.price
            if brieflisting.price>value['maxprice']:
                value['maxprice'] = brieflisting.price

    return housesoldpriceaverage, transactshomes

def AreaReportModelRunForSale(selected_zones, selectedhometypes,onsaledays):
    unfiltered_brieflistings = []
    zone_ids=[]
    for zone in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zone)
        if wzone:
            zone_ids.append(wzone.id)
            # unfiltered_brieflistings=unfiltered_brieflistings+wzone.brief_listings

    # current_time_ms = int(datetime.now().timestamp())  # Current time in milliseconds
    # time_threshold_ms = current_time_ms - (onsaledays * 24 * 60 * 60 )

    # forsalebrieflistings=[]
    # for brieflisting in unfiltered_brieflistings:
    #     try:
    #         if brieflisting.homeType not in selectedhometypes:
    #             continue
    #         if brieflisting.homeStatus!=FOR_SALE:
    #             continue
    #         if brieflisting.listtime < time_threshold_ms:  # Check if the listing is older than the threshold
    #             continue
    #         forsalebrieflistings.append(brieflisting)
    #     except Exception as e:
    #         print(f"Error processing brieflisting: {e}")

    forsalebrieflistings = brieflistingcontroller.listingsByZonesandStatus(zone_ids, FOR_SALE, onsaledays, selectedhometypes).all()
    housesoldpriceaverage={}
    # for brieflisting in forsalebrieflistings:
    #     try:
    #         # Create dynamic key based on bedrooms and bathrooms
    #         bed_bath_key = f"{int(brieflisting.bedrooms)}bed{int(brieflisting.bathrooms)}bath"
    #         # Initialize the dictionary for this key if it doesn't already exist
    #         if bed_bath_key not in housesoldpriceaverage:
    #             housesoldpriceaverage[bed_bath_key] = {
    #                 "count": 0,
    #                 "totalprice": 0,
    #                 "houses": []
    #             }
    #
    #         # Update the values for the current key
    #         housesoldpriceaverage[bed_bath_key]["count"] += 1
    #         housesoldpriceaverage[bed_bath_key]["totalprice"] += brieflisting.price
    #         housesoldpriceaverage[bed_bath_key]["houses"].append(brieflisting)
    #     except Exception as e:
    #         print(f"Error processing brieflisting: {e}")
    # # Create a map centered around Ballard, Seattle
    #
    # for key, value in housesoldpriceaverage.items():
    #     value['minprice']=1000000000
    #     value['maxprice']=0
    #     if value['count']==0:
    #         value['aveprice'] = 'NA'
    #     else:
    #         value['aveprice']= int(value['totalprice']/value['count'])
    #     for brieflisting in value["houses"]:
    #         if brieflisting.price<value['minprice']:
    #             value['minprice'] = brieflisting.price
    #         if brieflisting.price>value['maxprice']:
    #             value['maxprice'] = brieflisting.price



    return housesoldpriceaverage, forsalebrieflistings



def displayModel(neighbourhoods, selectedhometypes):
    unfiltered_soldhomes=brieflistingcontroller.ListingsByNeighbourhoodsAndHomeTypes(neighbourhoods, selectedhometypes, 30, 'RECENTLY_SOLD')
    df = pd.DataFrame([brieflisting.__dict__ for brieflisting in unfiltered_soldhomes])
    df = df.select_dtypes(include=['number'])
    print(df)
    features = df[['bathrooms', 'bedrooms', 'lotAreaValue','taxAssessedValue',]]  # Adjust based on your model
    target = df['price']
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    # Fit the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    living_area = X_test['taxAssessedValue']
    actual_prices = y_test
    predicted_prices = predictions
    errors = predicted_prices - actual_prices

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('Living Area (sqft)')
    ax1.set_ylabel('Actual Price', color=color)
    ax1.scatter(living_area, actual_prices, color=color, label='Actual Price', alpha=0.6)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xlim(0, 100)
    ax1.grid(which='major', linestyle='-', linewidth='0.5', color='blue')
    # Instantiate a second y-axis to plot the error
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Error ($)', color=color)  # we already handled the x-label with ax1
    ax2.scatter(living_area, errors, color=color, label='Error', alpha=0.6)
    ax2.tick_params(axis='y', labelcolor=color)

    # Show plot
    fig.tight_layout()  # To ensure there's no clipping of y-label
    plt.title('Actual Price vs. Living Area and Prediction Error')
    buf2 = BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)

    return base64.b64encode(buf2.read()).decode('utf-8')


def gatherCustomerData(customer_id, selected_doz, skip_plotting=False):
    import time
    t_start = time.time()
    print(f"[GATHER TIMING] gatherCustomerData START (skip_plotting={skip_plotting})")

    t1 = time.time()
    customer = customerzonecontroller.get_customer_zone(customer_id)
    # customer = customerzonecontroller.get_customer(customer_id)
    print(f"[GATHER TIMING] Get customer: {time.time() - t1:.2f}s")

    if not customer:
        return None, None, None
    homeType=None
    forsalehomes=[]#SW.SINGLE_FAMILY
    locations=[]
    locationzonenames=[]
    # Loop through neighborhoods to extract data when city is 'Seattle'
    # customerzpidcontroller

    #Main City Function this is for customers that we don't have a lot of info on yet.
    ## if zone len is zero that means we only know their main city but not the details.
    t2 = time.time()
    zones=[]
    if len(customer.zones) ==0:
        wcity = washingtoncitiescontroller.getCity(customer.maincity.City)
        if wcity:
            zones= washingtonzonescontroller.getZoneListbyCity_id(wcity.city_id)
        else:
            zones = washingtonzonescontroller.getzonebyName(customer.maincity.City)
    else:
        for customerzone in customer.zones:
            zones.append(washingtonzonescontroller.getZonebyID(customerzone.zone_id))
    print(f"[GATHER TIMING] Get {len(zones)} zones: {time.time() - t2:.2f}s")

    t3 = time.time()
    for zone in zones:
        # city_name = area["city"]  # Assuming `city` is in the returned dictionary
        print(zone.__str__())
        area={}
        zonestats = zonestatscachecontroller.get_zone_stats_by_zone(zone)
        locationzonenames.append(zone.zonename())
        area["zone"]=zone.zonename()
        area["zone_id"] = zone.id
        # if city_name == "Seattle":
        #     # Query the database to fetch the full row for this neighborhood
        #
        #
        #     forsalehomes= forsalehomes + brieflistingcontroller.forSaleListingsByCity(city_name, 365, homeType=homeType,
        #                                                                      neighbourhood_sub=area["neighbourhood_sub"]).all()
        if zonestats:
            area["forsale"]=zonestats.forsale
            area["pending7_SFH"] = zonestats.pending7_SFH
            area["pending7_TCA"] = zonestats.pending7_TCA
            area["sold7_SFH"] = zonestats.sold7_SFH
            area["sold7_TCA"] = zonestats.sold7_TCA
            area["forsaleadded7_SFH"] = zonestats.forsaleadded7_SFH
            area["forsaleadded7_TCA"] = zonestats.forsaleadded7_TCA
            area["sold"] = zonestats.sold
            locations.append(area)
    print(f"[GATHER TIMING] Process {len(zones)} zones & stats: {time.time() - t3:.2f}s")

    t4 = time.time()
    aicomments = ailistingcontroller.retrieve_ai_evaluation(customer_id)
    print(f"[GATHER TIMING] Retrieve {len(aicomments)} AI comments: {time.time() - t4:.2f}s")
    customerlistings=[]
    selectedaicomments=[]
    ai_comment_zpid=[]
    ai_suggestion_map_data = []

    t5 = time.time()
    for (idx,aicomment) in enumerate(aicomments, start=1):
        print(aicomment.listing.homeStatus)
        if aicomment.listing.homeStatus !=FOR_SALE:
            continue
        selectedaicomments.append((aicomment,aicomment.listing))
        customerlistings.append(aicomment.listing )
        ai_comment_zpid.append(aicomment.listing.zpid)
        ai_suggestion_map_data.append({
            "index": idx,
            "zpid": getattr(aicomment.listing, "zpid", None),
            "latitude": getattr(aicomment.listing, "latitude", None),
            "longitude": getattr(aicomment.listing, "longitude", None),
            "streetAddress": getattr(aicomment.listing, "streetAddress", None),
            "price": getattr(aicomment.listing, "price", None),
            # If you want more fields, add them here
        })
        if selectedaicomments.__len__()>10:
            break
    print(f"[GATHER TIMING] Process AI comments: {time.time() - t5:.2f}s")

    print("Running Area Sold Report")
    t6 = time.time()
    housesoldpriceaverage, soldhomes = AreaReportModelRun(locationzonenames,
                                                                               [SW.TOWNHOUSE, SW.SINGLE_FAMILY], selected_doz)
    print(f"[GATHER TIMING] AreaReportModelRun (sold): {time.time() - t6:.2f}s, {len(soldhomes)} homes")

    t7 = time.time()
    if skip_plotting:
        # Skip plotting to save time (~10s) - sold house tab is hidden
        plot_url = None
        plot_url2 = None
        print(f"[GATHER TIMING] Skipped plotting (sold tab hidden)")
    else:
        plot_url = createPriceChangevsDays2PendingPlot(soldhomes)
        plot_url2= createPricevsDays2PendingPlot(soldhomes)
        print(f"[GATHER TIMING] Create 2 plots: {time.time() - t7:.2f}s")

    print("Running Area Sale Report")
    t8 = time.time()
    asdf, forsalebrieflistings = AreaReportModelRunForSale(locationzonenames, [SW.TOWNHOUSE, SW.SINGLE_FAMILY],
                                                                            365)
    print(f"[GATHER TIMING] AreaReportModelRunForSale: {time.time() - t8:.2f}s, {len(forsalebrieflistings)} homes")

    print(f"[GATHER TIMING] gatherCustomerData TOTAL: {time.time() - t_start:.2f}s")

    return (customer, locations , locationzonenames , customerlistings , housesoldpriceaverage,
            plot_url, plot_url2, soldhomes , forsalebrieflistings,
            selectedaicomments,ai_comment_zpid , ai_suggestion_map_data)
