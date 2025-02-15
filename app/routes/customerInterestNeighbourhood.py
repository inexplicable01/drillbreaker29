# email_bp.py
from datetime import datetime
import pytz
from app.DBFunc.CityStatsCacheController import citystatscachecontroller
from flask import flash,Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,ListAllNeighhourhoodsByCities
from app.config import Config,SW
customer_interest_bp = Blueprint('customer_interest_bp', __name__, url_prefix='/customer_interest')
from app.DBFunc.CustomerNeighbourhoodInterestController import customerneighbourhoodinterestcontroller
from app.DBFunc.CityStatsCacheController import citystatscachecontroller
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

    if customerzpidcontroller.retire_customer_zpid(customer_id, zpid):
        return redirect(url_for('customer_interest_bp.listCustomersforAlerts')) # customer_list renders the table
    else:
        return "ZPID not found or unable to retire", 404
    # Query the specific ZPID for the customer and mark it as retired





def gatherCustomerData(customer_id):
    customer_data, locations = customerneighbourhoodinterestcontroller.get_customer_neighbourhood_interest(customer_id)
    customer = customerneighbourhoodinterestcontroller.get_customer(customer_id)

    if not customer:
        return None, None, None, None, None
    homeType=None
    forsalehomes=[]#SW.SINGLE_FAMILY
    # Loop through neighborhoods to extract data when city is 'Seattle'
    for area in locations:
        city_name = area["city"]  # Assuming `city` is in the returned dictionary

        if city_name == "Seattle":
            # Query the database to fetch the full row for this neighborhood
            print(f"{city_name}, {area['neighbourhood_sub']}")
            city_row = citystatscachecontroller.get_city_stats_by_name(city_name,area["neighbourhood_sub"])
            forsalehomes= forsalehomes + brieflistingcontroller.forSaleListingsByCity(city_name, 365, homeType=homeType,
                                                                             neighbourhood_sub=area["neighbourhood_sub"]).all()
            if city_row:
                area["forsale"]=city_row.forsale
                area["pending7_SFH"] = city_row.pending7_SFH
                area["pending7_TCA"] = city_row.pending7_TCA
                area["sold7_SFH"] = city_row.sold7_SFH
                area["sold7_TCA"] = city_row.sold7_TCA
                area["forsaleadded7_SFH"] = city_row.forsaleadded7_SFH
                area["forsaleadded7_TCA"] = city_row.forsaleadded7_TCA
                area["sold"] = city_row.sold
        else:
            city_row = citystatscachecontroller.get_city_stats_by_name(city_name)
            forsalehomes= forsalehomes + brieflistingcontroller.forSaleListingsByCity(city_name, 365, homeType=homeType
                                                                              ).all()
            print(f"{city_name}")
            if city_row:
                area["forsale"]=city_row.forsale
                area["pending7_SFH"] = city_row.pending7_SFH
                area["pending7_TCA"] = city_row.pending7_TCA
                area["sold7_SFH"] = city_row.sold7_SFH
                area["sold7_TCA"] = city_row.sold7_TCA
                area["forsaleadded7_SFH"] = city_row.forsaleadded7_SFH
                area["forsaleadded7_TCA"] = city_row.forsaleadded7_TCA
                area["sold"] = city_row.sold
    neighbourhoods_subs = []
    cities = []
    for n in locations:
        neighbourhoods_subs.append(n["neighbourhood_sub"])
        cities.append(n["city"])

    return customer, locations, cities, neighbourhoods_subs, forsalehomes



@customer_interest_bp.route('/send_email/<int:customer_id>', methods=['POST'])
def send_email(customer_id):
    # Query the customer and their interests
    # customer = Customer.query.get(customer_id)

    customer, locations, cities, neighbourhoods_subs, forsalehomes = gatherCustomerData(customer_id)

    if not customer:
        return "No customers found", 404
    sendCustomerEmail(customer,locations, cities, neighbourhoods_subs, forsalehomes)

    # Redirect back to the same interests page after sending email
    return redirect(url_for('customer_interest_bp.displayCustomerInterest', customer_id=customer_id))

from pathlib import Path
import os
@customer_interest_bp.route('/all', methods=['GET','POST'])
def displayCustomerInterest():
    # Fetch precomputed city stats from the cache
    # Mock data for the example
    customer_id = request.args.get("customer_id", type=int, default=None)

    customer, locations, cities, neighbourhoods_subs, forsalehomes = gatherCustomerData(customer_id)

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
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists
    map_html_path = output_dir / f"map_{customer.name}.html"
    map_image_path = output_dir / f"map_{customer.name}_screenshot.png"
    url_image_path= f"maps/map_{customer.name}_screenshot.png"
    # # Step 1: Generate map HTML

    if not os.path.exists(map_html_path):
        map_html = create_map(
            geojson_features=geojson_features,
            neighbourhoods_subs=neighbourhoods_subs,
            cities=cities,
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
                           cities=cities,
                           neighbourhoods_subs=neighbourhoods_subs,
                           geojson_features= WA_geojson_features,
                           homes_with_comments=homes_with_comments,
                           url_image_path=url_image_path
                           )





# @citystats_bp.route('/update', methods=['POST'])
# def update_city_stats():
#     try:
#         cities = washingtoncitiescontroller.getallcities()
#         citystatscachecontroller.refresh_city_stats(cities, brieflistingcontroller)
#         return jsonify({"status": "success", "message": "City stats updated successfully."})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
@customer_interest_bp.route('/get_neighbourhood_details', methods=['GET','POST'])
def get_neighbourhood_details():
    data = request.get_json()
    city = data.get('city')

    neighbourhood_sub = data.get('neighbourhood_sub')
    if neighbourhood_sub=='None':
        neighbourhood_sub = None

    city_stats = citystatscachecontroller.get_city_stats_by_name(city, neighbourhood_sub)

    sold7_SFH = brieflistingcontroller.soldListingsByCity(city, 7, homeType=SW.SINGLE_FAMILY, neighbourhood_sub=neighbourhood_sub).all()
    sold7_TCA = brieflistingcontroller.soldListingsByCity(city, 7,
                                                          homeType=[SW.APARTMENT, SW.TOWNHOUSE, SW.CONDO],
                                                          neighbourhood_sub=neighbourhood_sub).all()

    pending7_SFH = brieflistingcontroller.pendingListingsByCity(city, 7, homeType=SW.SINGLE_FAMILY, neighbourhood_sub=neighbourhood_sub).all()
    pending7_TCA = brieflistingcontroller.pendingListingsByCity(city, 7, homeType=[SW.APARTMENT, SW.TOWNHOUSE,SW.CONDO],
                                                                neighbourhood_sub=neighbourhood_sub).all()
    # # pending7_Other=brieflistingcontroller.pendingListingsByCity(city, 7).count(),
    #
    forsaleadded7_SFH = brieflistingcontroller.forSaleListingsByCity(city, 7, homeType=SW.SINGLE_FAMILY,
                                                                     neighbourhood_sub=neighbourhood_sub).all()
    forsaleadded7_TCA = brieflistingcontroller.forSaleListingsByCity(city, 7,
                                                                     homeType=[SW.APARTMENT, SW.TOWNHOUSE,SW.CONDO],
                                                                     neighbourhood_sub=neighbourhood_sub).all()

    sold7_SFH_homes = [brieflisting.to_dict() for brieflisting in sold7_SFH] if sold7_SFH else []
    sold7_TCA_homes = [brieflisting.to_dict() for brieflisting in sold7_TCA] if sold7_TCA else []
    pending7_SFH_homes = [brieflisting.to_dict() for brieflisting in pending7_SFH] if pending7_SFH else []
    pending7_TCA_homes = [brieflisting.to_dict() for brieflisting in pending7_TCA] if pending7_TCA else []
    forsaleadded7_SFH_homes = [brieflisting.to_dict() for brieflisting in forsaleadded7_SFH] if forsaleadded7_SFH else []
    forsaleadded7_TCA_homes = [brieflisting.to_dict() for brieflisting in forsaleadded7_TCA] if forsaleadded7_TCA else []

    return jsonify({
        "html": render_template('components/neighbourhood_details_card.html',
                                 city=city,
                                 neighbourhood_sub=neighbourhood_sub,
                                 recent_sales=city_stats.sold,
                                 avg_price=city_stats.avg_price if hasattr(city_stats, 'avg_price') else "N/A",
                                 trends=city_stats.trends if hasattr(city_stats, 'trends') else "N/A",
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
    customer_data, locations = customerneighbourhoodinterestcontroller.get_customer_neighbourhood_interest(3)
    customer = customerneighbourhoodinterestcontroller.get_customer(customer_id)

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


