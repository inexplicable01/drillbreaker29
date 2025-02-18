# email_bp.py
from datetime import datetime
import pytz
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from flask import Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,ListAllNeighhourhoodsByCities
from app.config import Config,SW
zonestats_bp = Blueprint('zonestats_interesting', __name__, url_prefix='/zonestats')
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBFunc.WashingtonZonesController import   washingtonzonescontroller

@zonestats_bp.route('/basics', methods=['GET','POST'])
def zonestats():
    # Fetch precomputed city stats from the cache
    zonesdata = zonestatscachecontroller.get_all_zone_stats()
    seattle_tz = pytz.timezone('America/Los_Angeles')
    # Convert the cached data to a format suitable for rendering in the template
    formatted_data = [
        {
            'name': zone.city_name,
            'sold': zone.sold,
            'sold7_SFH': zone.sold7_SFH,
            'sold7_TCA': zone.sold7_TCA,
            'pending': zone.pending,
            'pending7_SFH': zone.pending7_SFH,
            'pending7_TCA': zone.pending7_TCA,
            'pending1': zone.pending1,
            'forsale': zone.forsale,
            'forsaleadded7_SFH': zone.forsaleadded7_SFH,
            'forsaleadded7_TCA': zone.forsaleadded7_TCA,
            'updated': zone.updated_time.astimezone(seattle_tz).strftime(
                '%m/%d/%Y %I:%M %p %A') if zone.updated_time else "N/A"
        }
        for zone in zonesdata
    ]

    return render_template('TransactionTable.html', citiesdata=formatted_data)


@zonestats_bp.route('/update', methods=['POST'])
def update_zone_stats():
    try:
        # cities = washingtoncitiescontroller.getallcities()
        zones =washingtonzonescontroller.getlist()
        zonestatscachecontroller.refresh_zone_stats(zones)
        return jsonify({"status": "success", "message": "City stats updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# @zonestats_bp.route('/update', methods=['POST'])
# def update_zone_stats():
#     try:
#         cities = washingtoncitiescontroller.getallcities()
#         zonestatscachecontroller.refresh_zone_stats(cities, brieflistingcontroller)
#         return jsonify({"status": "success", "message": "City stats updated successfully."})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500




