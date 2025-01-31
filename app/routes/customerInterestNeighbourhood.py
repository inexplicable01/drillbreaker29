# email_bp.py
from datetime import datetime
import pytz
from app.DBFunc.CityStatsCacheController import citystatscachecontroller
from flask import Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,ListAllNeighhourhoodsByCities
from app.config import Config,SW
customer_interest_bp = Blueprint('customer_interest_bp', __name__, url_prefix='/customer_interest')
from app.DBFunc.CustomerNeighbourhoodInterestController import customerneighbourhoodinterestcontroller
from app.DBFunc.CityStatsCacheController import citystatscachecontroller

@customer_interest_bp.route('/all', methods=['GET','POST'])
def displayCustomerInterest():
    # Fetch precomputed city stats from the cache
    # Mock data for the example
    customer_id=3
    customer, neighbourhoods = customerneighbourhoodinterestcontroller.get_customer_neighbourhood_interest(customer_id)

    # I want to loop through neiughbourhoods and extract that data here.

    if not customer:
        return f"Customer with ID {customer_id} not found", 404

    city_data = []

    # Loop through neighborhoods to extract data when city is 'Seattle'
    for area in neighbourhoods:
        city_name = area["city"]  # Assuming `city` is in the returned dictionary

        if city_name == "Seattle":
            # Query the database to fetch the full row for this neighborhood
            city_row = citystatscachecontroller.get_city_stats_by_name(city_name,area["neighbourhood_sub"])

            if city_row:
                area["forsale"]=city_row.forsale
                area["pending7_SFH"] = city_row.pending7_SFH
                area["pending7_TCA"] = city_row.pending7_TCA
                area["sold7_SFH"] = city_row.sold7_SFH
                area["sold7_TCA"] = city_row.sold7_TCA
                area["forsaleadded7_SFH"] = city_row.forsaleadded7_SFH
                area["forsaleadded7_TCA"] = city_row.forsaleadded7_TCA
                area["sold"] = city_row.sold
                # city_data.append({
                #     "city_name": city_row.city_name,
                #     "sold": city_row.sold,
                #     "pending": city_row.pending,
                #     "forsale": city_row.forsale,
                #     "updated_time": city_row.updated_time,
                #     "neighbourhood": neighbourhood.get("neighbourhood", ""),
                #     "neighbourhood_sub": neighbourhood.get("neighbourhood_sub", "")
                # })

    return render_template('NeighbourhoodInterest.html', customer=customer, neighbourhoods=neighbourhoods)

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



