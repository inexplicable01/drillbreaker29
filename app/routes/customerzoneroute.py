# email_bp.py
from datetime import datetime
import pytz

from app.DBFunc.WashingtonZonesController import WashingtonZonesController, washingtonzonescontroller
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from flask import flash,Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,AreaReportModelRunForSale
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE, PENDING

customer_interest_bp = Blueprint('customer_interest_bp', __name__, url_prefix='/customer_interest')
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from app.DBFunc.AIListingController import ailistingcontroller
from app.DBFunc.CustomerController import customercontroller
from app.MapTools.MappingTools import WA_geojson_features, create_map
from app.RouteModel.AIModel import AIModel
from app.RouteModel.EmailModel import sendCustomerEmail
from app.DBFunc.CustomerZpidController import customerzpidcontroller
from app.ZillowAPI.ZillowAPICall import SearchZilowByMLSID, SearchZillowByZPID


@customer_interest_bp.route('/customers', methods=['GET'])
def listCustomers():
    # Fetch all customers from the database (pseudo-code function)
    customers = customercontroller.getAllCustomer()

    if not customers:
        return "No customers found", 404

    return render_template('CustomerList.html', customers=customers)


@customer_interest_bp.route('/listCustomersforAlerts', methods=['GET'])
def listCustomersforAlerts():
    # Fetch all customers from the database (pseudo-code function)
    customers = customercontroller.getCustomerZpidInterests()

    if not customers:
        return "No customers found", 404

    return render_template('CustomerList_wAlerts.html', customers=customers)


@customer_interest_bp.route('/customer_interests')
def display_customer_interests():
    # Preload brief_listings using joinedload for optimized queries
    customers = customercontroller.getCustomerZpidInterests()
    return render_template('customer_interest.html', customers=customers)

@customer_interest_bp.route('/save_zpid', methods=['POST'])
def save_zpid():
    customer_id = request.form.get('customer_id')  # Retrieve customer ID from the form
    NWMLS_id = request.form.get('NWMLS_id')       # Retrieve MLS ID (highest priority)
    zpid = request.form.get('zpid')              # Retrieve ZPID (fallback)

    customer = customercontroller.getCustomerByID(customer_id)

    if not customer:
        print("Customer not found.", "error")
        return "Customer not found.", 400

    # Step 2: Try to fetch the brieflisting using NWMLS_id first.
    brieflisting = None
    if NWMLS_id:
        brieflisting = brieflistingcontroller.get_listing_by_mls_id(NWMLS_id)
    elif zpid:
        # Fallback to zpid if NWMLS_id is not provided
        brieflisting = brieflistingcontroller.get_listing_by_zpid(zpid)

    if not brieflisting:
        if NWMLS_id:
            print(f"Listing with NWMLS_id '{NWMLS_id}' not found, attempting to fetch via Zillow API...")
            zpid = SearchZilowByMLSID(NWMLS_id)  # Attempt API lookup with MLS ID
            if zpid:
                propertydata = SearchZillowByZPID(zpid)
                brieflisting = brieflistingcontroller.CreateBriefListingFromPropertyData(propertydata)
                brieflistingcontroller.updateBriefListing(brieflisting)
        elif zpid:
            print(f"Listing with ZPID '{zpid}' not found, attempting to fetch via Zillow API...")
            propertydata = SearchZillowByZPID(zpid)  # Attempt API lookup with ZPID
            brieflisting = brieflistingcontroller.CreateBriefListingFromPropertyData(propertydata)
            brieflistingcontroller.updateBriefListing(brieflisting)
        else:
            # If neither NWMLS_id nor ZPID exists, don't proceed with saving
            print("No NWMLS_id or ZPID provided. Cannot find listing.", "error")
            return "No NWMLS_id or ZPID provided. Cannot find listing.", 400


    if brieflisting:
        customerzpidcontroller.saveCustomerzpid(brieflisting, customer)  # Save the relationship to DB
        flash("ZPID saved successfully!", "success")  # Flash a success message
        return redirect(url_for('customer_interest_bp.listCustomersforAlerts'))
    else:
        flash("Failed to fetch brieflisting from Zillow API.", "error")  # Flash an error message
        return redirect(url_for('customer_interest_bp.listCustomersforAlerts'))

    return redirect(url_for('customer_interest_bp.listCustomersforAlerts'))  # Replace 'customer_list' with your route name

@customer_interest_bp.route('/retire_zpid', methods=['POST'])
def retire_zpid():
    customer_id = request.form['customer_id']
    zpid = request.form['zpid']
    customerzpid_id = request.form['customerzpid_id']
    if customerzpidcontroller.retire_customer_zpid(customerzpid_id):
        return redirect(url_for('customer_interest_bp.listCustomersforAlerts')) # customer_list renders the table
    else:
        return "ZPID not found or unable to retire", 404
    # Query the specific ZPID for the customer and mark it as retired





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
    for customerzone in customer.zones:
        city_name = customerzone.zone.City
        # city_name = area["city"]  # Assuming `city` is in the returned dictionary
        print(customerzone.zone.__str__())
        area={}
        zonestats = zonestatscachecontroller.get_zone_stats_by_zone(customerzone.zone)
        locationzonenames.append(customerzone.zone.zonename())
        area["zone"]=customerzone.zone.zonename()
        area["zone_id"] = customerzone.zone.id
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
    customerlistings = brieflistingcontroller.getListingByCustomerPreference(customer, FOR_SALE, 90)
    housesoldpriceaverage, plot_url, plot_url2, soldhomes = AreaReportModelRun(locationzonenames,
                                                                               [SW.TOWNHOUSE, SW.SINGLE_FAMILY], selected_doz)

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


    return customer, locations , locationzonenames , customerlistings , housesoldpriceaverage, plot_url, plot_url2, soldhomes , forsalehomes_dict, brieflistings_SoldHomes_dict
    # return customer, locations, cities, neighbourhoods_subs, forsalehomes



@customer_interest_bp.route('/send_email/<int:customer_id>', methods=['POST'])
def send_email(customer_id):
    # Query the customer and their interests
    # customer = Customer.query.get(customer_id)

    customer, locations, locationzonenames, customerlistings,housesoldpriceaverage, plot_url, plot_url2, soldhomes, forsalehomes_dict, brieflistings_SoldHomes_dict  = gatherCustomerData(customer_id, selected_doz)

    if not customer:
        return "No customers found", 404
    sendCustomerEmail(customer,locations, plot_url, soldhomes)

    # Redirect back to the same interests page after sending email
    return redirect(url_for('customer_interest_bp.displayCustomerInterest', customer_id=customer_id))

from pathlib import Path
import os
@customer_interest_bp.route('/all', methods=['GET','POST'])
def displayCustomerInterest():
    # Fetch precomputed city stats from the cache
    # Mock data for the example
    customer_id = request.args.get("customer_id", type=int, default=None)
    selected_doz=30
    customer, locations, locationzonenames, customerlistings,housesoldpriceaverage, plot_url, plot_url2, soldhomes, forsalehomes_dict, brieflistings_SoldHomes_dict\
        = gatherCustomerData(customer_id, selected_doz)

    aicomments=[]
    selectedhomes=[]
    homes_with_comments=[]
    # for brieflisting in forsalehomes:
    #     ai_comment = ailistingcontroller.check_existing_evaluation(customer_id, brieflisting.zpid)
    #     if ai_comment and ai_comment.likelihood_score>50:
    #         selectedhomes.append(brieflisting)
    #         aicomments.append(ai_comment)
    # homes_with_comments = list(zip(selectedhomes, aicomments))

    geojson_features = WA_geojson_features  # Replace `WA_geojson_features` with your actual data

    # Define file paths
    output_dir = Path("app/static/maps")
    map_html_path = output_dir / f"map_{customer.name}.html"
    map_image_path = output_dir / f"map_{customer.name}_screenshot.png"
    url_image_path= f"maps/map_{customer.name}_screenshot.png"
    # # Step 1: Generate map HTML

    if not os.path.exists(map_html_path):
        map_html = create_map(
            geojson_features=geojson_features,
            neighbourhoods_subs=locationzonenames,
            cities=locationzonenames,
            map_html_path=str(map_html_path),
            map_image_path = str(map_image_path)
        )

    # Step 2: Capture map as an image
    # save_map_as_image(map_html_path=str(map_html_path), output_image_path=str(map_image_path))

    # Step 3: Serve the map image in the template
    map_image_url = f"/static/maps/{map_image_path.name}"




    return render_template('InterestReport/NeighbourhoodInterest.html',
                           customer=customer,
                           Webpage=True,
                           locations=locations,
                           locationzonenames= locationzonenames,
                           geojson_features= WA_geojson_features,
                           homes_with_comments=homes_with_comments,
                           url_image_path=url_image_path,
                           plot_url=plot_url,
                           soldhouses=soldhomes,
                           forsalehomes_dict=forsalehomes_dict,
                           selected_doz=selected_doz,
                           customerlistings=customerlistings,
                           selected_zones = locationzonenames,
                           brieflistings_SoldHomes_dict = brieflistings_SoldHomes_dict
                           )





# @zonestats_bp.route('/update', methods=['POST'])
# def update_zone_stats():
#     try:
#         cities = washingtoncitiescontroller.getallcities()
#         zonestatscachecontroller.refresh_zone_stats(cities, brieflistingcontroller)
#         return jsonify({"status": "success", "message": "City stats updated successfully."})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
@customer_interest_bp.route('/get_zone_details', methods=['GET','POST'])
def get_zone_details():
    data = request.get_json()
    zone_id = data.get('zone_id')

    zone = washingtonzonescontroller.getZonebyID(zone_id)

    zone_stats = zonestatscachecontroller.get_zone_stats_by_zone(zone)

    sold7_SFH = brieflistingcontroller.listingsByZoneandStatus(zone, RECENTLYSOLD, 7, homeType=SW.SINGLE_FAMILY).all()
    sold7_TCA = brieflistingcontroller.listingsByZoneandStatus(zone, RECENTLYSOLD, 7,
                                                          homeType=[SW.APARTMENT, SW.TOWNHOUSE, SW.CONDO]).all()

    pending7_SFH = brieflistingcontroller.listingsByZoneandStatus(zone, PENDING, 7, homeType=SW.SINGLE_FAMILY).all()
    pending7_TCA = brieflistingcontroller.listingsByZoneandStatus(zone, PENDING,7, homeType=[SW.APARTMENT, SW.TOWNHOUSE,SW.CONDO]).all()
    # # pending7_Other=brieflistingcontroller.pendingListingsByCity(city, 7).count(),
    #
    forsaleadded7_SFH = brieflistingcontroller.listingsByZoneandStatus(zone, FOR_SALE, 7, homeType=SW.SINGLE_FAMILY).all()
    forsaleadded7_TCA = brieflistingcontroller.listingsByZoneandStatus(zone, FOR_SALE, 7,
                                                                     homeType=[SW.APARTMENT, SW.TOWNHOUSE,SW.CONDO]).all()

    sold7_SFH_homes = [brieflisting.to_dict() for brieflisting in sold7_SFH] if sold7_SFH else []
    sold7_TCA_homes = [brieflisting.to_dict() for brieflisting in sold7_TCA] if sold7_TCA else []
    pending7_SFH_homes = [brieflisting.to_dict() for brieflisting in pending7_SFH] if pending7_SFH else []
    pending7_TCA_homes = [brieflisting.to_dict() for brieflisting in pending7_TCA] if pending7_TCA else []
    forsaleadded7_SFH_homes = [brieflisting.to_dict() for brieflisting in forsaleadded7_SFH] if forsaleadded7_SFH else []
    forsaleadded7_TCA_homes = [brieflisting.to_dict() for brieflisting in forsaleadded7_TCA] if forsaleadded7_TCA else []

    return jsonify({
        "html": render_template('components/neighbourhood_details_card.html',
                                 zonename=zone.zonename(),
                                 recent_sales=zone_stats.sold,
                                 avg_price=zone_stats.avg_price if hasattr(zone_stats, 'avg_price') else "N/A",
                                 trends=zone_stats.trends if hasattr(zone_stats, 'trends') else "N/A",
                                 sold7_SFH=sold7_SFH_homes,
                                sold7_TCA=sold7_TCA_homes,
                                pending7_SFH=pending7_SFH_homes,
                                pending7_TCA=pending7_TCA_homes,
                                forsaleadded7_SFH=forsaleadded7_SFH_homes,
                                forsaleadded7_TCA=forsaleadded7_TCA_homes,
                                )
    })

@customer_interest_bp.route("/evaluate_listing", methods=["POST"])
def evaluate_listing():
    """
    API endpoint to evaluate a listing's match likelihood for a customer.
    """
    customer_id=3
    data = request.json
    zpid = data.get("zpid")
    customer_data, locations = customerzonecontroller.get_customer_zone(3)
    customer = customerzonecontroller.get_customer(customer_id)

    existing_comment = ailistingcontroller.check_existing_evaluation(customer_id, zpid)

    if existing_comment:
        return jsonify({
            "message": "AI evaluation already exists.",
            "likelihood_score": existing_comment.likelihood_score,
            "reason": existing_comment.ai_comment
        }), 200

    if not zpid:
        return jsonify({"error": "Missing ZPID"}), 400

    ai_response  = AIModel(zpid,  customer, locations)

    if "error" in ai_response:
        return jsonify(ai_response), 500

    # Extract AI results
    likelihood_score = ai_response.get("likelihood_score", 0)
    ai_comment = ai_response.get("reason", "")

    # Save AI results to database
    ailistingcontroller.save_ai_evaluation(
        customer_id=customer_id,
        zpid=zpid,
        ai_comment=ai_comment,
        likelihood_score=likelihood_score
    )


    return jsonify({
        "message": "AI evaluation saved successfully",
        "likelihood_score": likelihood_score,
        "reason": ai_comment
    }), 201


