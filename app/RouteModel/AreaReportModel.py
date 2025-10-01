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

def StatsModelRun(zone_ids, daysofconcern, daysofconcernforlistings=7):
    # --- helpers (local to keep the function self-contained) ---
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
        """
        Convert br.soldtime (Unix epoch) -> date.
        Accepts int/float/str; tolerates milliseconds.
        Returns a datetime.date or None.
        """
        ts = getattr(br, "soldtime", None)
        if ts is None:
            return None
        try:
            ts = float(ts)
            # if it's in milliseconds (13 digits), normalize to seconds
            if ts > 1e12:
                ts /= 1000.0
            return datetime.utcfromtimestamp(ts).date()
        except Exception:
            return None

    def _week_start(d: date) -> date:
        # Monday anchor
        return d - timedelta(days=d.weekday())

    # --- existing aggregations (unchanged) ---
    fastest_days = 10
    fast_sales = 0
    under_list = 0
    above_list = 0
    sold_prices = []
    sale_to_list_ratios = []
    list2penddayslist = []

    # Pull enough sold inventory to cover 16 weeks (112 days)
    sold_window_days = max(daysofconcernforlistings, 112)

    soldhomes = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD, sold_window_days).all()
    pending = brieflistingcontroller.listingsByZonesandStatus(zone_ids, PENDING, daysofconcernforlistings).all()
    new_listings = brieflistingcontroller.listingsByZonesandStatus(zone_ids, FOR_SALE, daysofconcernforlistings).all()

    brieflistings = soldhomes + pending
    for br in brieflistings:
        if br.list2penddays is not None:
            d = br.list2penddays
            if d < fastest_days:
                fastest_days = d
            if d < 8:
                fast_sales += 1
            list2penddayslist.append(d)

        if br.listprice is not None and br.soldprice is not None and br.listprice > 0:
            if br.soldprice < br.listprice:
                under_list += 1
            else:
                above_list += 1
            sold_prices.append(br.soldprice)
            sale_to_list_ratios.append(100.0 * (br.soldprice / br.listprice))

    total_with_days = len(list2penddayslist)
    median_days = statistics.median(list2penddayslist) if total_with_days else None
    avg_days_on_market = statistics.mean(list2penddayslist) if total_with_days else None
    avg_sold_price = statistics.mean(sold_prices) if sold_prices else None
    median_sold_price = statistics.median(sold_prices) if sold_prices else None

    basis_comp = (under_list + above_list) or 0
    pct_over_ask = (100.0 * above_list / basis_comp) if basis_comp else 0.0
    sale_to_list_avg_pct = statistics.mean(sale_to_list_ratios) if sale_to_list_ratios else None
    pct_under_7d = (100.0 * fast_sales / total_with_days) if total_with_days else 0.0
    pct_price_cuts = under_list/len(brieflistings)# TODO: set if you track cuts

    # --- new: 16-week (weekly) median price time series ---
    today = datetime.utcnow().date()
    this_monday = _week_start(today)
    # Build week starts oldest→newest (16 weeks including this week)
    week_starts = [this_monday - timedelta(weeks=i) for i in range(15, -1, -1)]
    buckets = {ws: [] for ws in week_starts}

    for br in soldhomes:  # only look at sold homes for the price series
        sd = _sold_date_for(br)
        if not sd:
            continue
        # Only include if within our 16-week window
        if sd < week_starts[0] or sd > (week_starts[-1] + timedelta(days=6)):
            continue
        ws = _week_start(sd)
        if ws in buckets:
            sp = getattr(br, "soldprice", None)
            if sp is not None:
                buckets[ws].append(sp)

    median_price_16w = []
    for ws in week_starts:
        values = buckets.get(ws, [])
        if values:
            mp = int(round(statistics.median(values)))
            cnt = len(values)
        else:
            mp = None
            cnt = 0
        median_price_16w.append({
            "week_start": ws.isoformat(),
            "median_price": mp,  # raw number; format later in Jinja if needed
            "count": cnt
        })

    return {
        # existing
        "total_sold": len(soldhomes),
        "total_pending": len(pending),
        "new_listings": len(new_listings),
        "fast_sales": fast_sales,
        "under_list": under_list,
        "above_list": above_list,
        "fastest_days": fastest_days,
        "median_days": median_days,
        "avg_days_on_market": avg_days_on_market,
        "avg_sold_price": avg_sold_price,
        "median_sold_price": median_sold_price,
        "pct_over_ask": pct_over_ask,
        "sale_to_list_avg_pct": sale_to_list_avg_pct,
        "pct_under_7d": pct_under_7d,
        "pct_price_cuts": pct_price_cuts,

        # new series
        "median_price_16w": median_price_16w,  # ← list of {week_start, median_price, count}
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


def gatherCustomerData(customer_id, selected_doz):
    customer = customerzonecontroller.get_customer_zone(customer_id)
    # customer = customerzonecontroller.get_customer(customer_id)

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
        # else:
        #     city_row = zonestatscachecontroller.get_zone_stats_by_zone(city_name)
        #     forsalehomes= forsalehomes + brieflistingcontroller.forSaleListingsByCity(city_name, 365, homeType=homeType
        #                                                                       ).all()
        #     print(f"{city_name}")
        #     if city_row:
        #         area["forsale"]=city_row.forsale
        #         area["pending7_SFH"] = city_row.pending7_SFH
        #         area["pending7_TCA"] = city_row.pending7_TCA
        #         area["sold7_SFH"] = city_row.sold7_SFH
        #         area["sold7_TCA"] = city_row.sold7_TCA
        #         area["forsaleadded7_SFH"] = city_row.forsaleadded7_SFH
        #         area["forsaleadded7_TCA"] = city_row.forsaleadded7_TCA
        #         area["sold"] = city_row.sold


    # neighbourhoods_subs = []
    # cities = []
    # for n in locations:
    #     neighbourhoods_subs.append(n["neighbourhood_sub"])
    #     cities.append(n["city"])
    # customerlistings = brieflistingcontroller.getListingByCustomerPreference(customer, FOR_SALE, 90)
    aicomments = ailistingcontroller.retrieve_ai_evaluation(customer_id)
    customerlistings=[]
    selectedaicomments=[]
    ai_comment_zpid=[]
    for aicomment in aicomments:
        print(aicomment.listing.homeStatus)
        if aicomment.listing.homeStatus !=FOR_SALE:
            continue
        selectedaicomments.append((aicomment,aicomment.listing))
        customerlistings.append(aicomment.listing )
        ai_comment_zpid.append(aicomment.listing.zpid)
        if selectedaicomments.__len__()>10:
            break

    print("Running Area Sold Report")
    housesoldpriceaverage, soldhomes = AreaReportModelRun(locationzonenames,
                                                                               [SW.TOWNHOUSE, SW.SINGLE_FAMILY], selected_doz)

    plot_url = createPriceChangevsDays2PendingPlot(soldhomes)
    plot_url2= createPricevsDays2PendingPlot(soldhomes)

    print("Running Area Sale Report")
    asdf, forsalebrieflistings = AreaReportModelRunForSale(locationzonenames, [SW.TOWNHOUSE, SW.SINGLE_FAMILY],
                                                                            365)
    forsalehomes_dict=[]
    for brieflisting in forsalebrieflistings:
        if brieflisting.fsbo_status is None:
            forsalehomes_dict.append(brieflisting.to_dict())

    brieflistings_SoldHomes_dict=[]
    for brieflisting in soldhomes:
        if brieflisting.fsbo_status is None: # don't want to include fsbos cause it causes an error
            # hard code out for now.
            brieflistings_SoldHomes_dict.append(
               brieflisting.to_dict()
            )


    return (customer, locations , locationzonenames , customerlistings , housesoldpriceaverage,
            plot_url, plot_url2, soldhomes , forsalehomes_dict, brieflistings_SoldHomes_dict ,
            selectedaicomments,ai_comment_zpid)
