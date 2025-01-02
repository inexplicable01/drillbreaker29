# email_bp.py
from datetime import datetime
import pytz
from app.DBFunc.CityStatsCacheController import citystatscachecontroller
from flask import Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,ListAllNeighhourhoodsByCities
from app.config import Config,SW
citystats_bp = Blueprint('citystats_interesting', __name__, url_prefix='/citystats')
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller

@citystats_bp.route('/basics', methods=['GET','POST'])
def citystats():
    # Fetch precomputed city stats from the cache
    citiesdata = citystatscachecontroller.get_all_city_stats()
    seattle_tz = pytz.timezone('America/Los_Angeles')
    # Convert the cached data to a format suitable for rendering in the template
    formatted_data = [
        {
            'name': city.city_name,
            'sold': city.sold,
            'pending': city.pending,
            'forsale': city.forsale,
            'updated': city.updated_time.astimezone(seattle_tz).strftime(
                '%m/%d/%Y %I:%M %p %A') if city.updated_time else "N/A"
        }
        for city in citiesdata
    ]

    return render_template('TransactionTable.html', citiesdata=formatted_data)


@citystats_bp.route('/update', methods=['POST'])
def update_city_stats():
    try:
        cities = washingtoncitiescontroller.getallcities()
        citystatscachecontroller.refresh_city_stats(cities, brieflistingcontroller)
        return jsonify({"status": "success", "message": "City stats updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




