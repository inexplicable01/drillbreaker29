# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request, send_from_directory
# from app.DBFunc.BriefListingController import brieflistingcontroller
# from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
# from app.DBModels.BriefListing import BriefListing
# from app.config import Config, SW, RECENTLYSOLD
# # from flask import Flask, render_template, make_response
# # from weasyprint import HTML
# from app.MapTools.MappingTools import WA_geojson_features
# from app.DBFunc.CustomerZoneController import customerzonecontroller
# from app.RouteModel.AIModel import AIModel
# from app.DBFunc.AIListingController import ailistingcontroller
# from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
# from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
#     loadPropertyDataFromBrief, ListingStatus
# from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO, SearchZillowHomesByLocation
# from datetime import datetime
# from app.RouteModel.BriefListingsVsApi import ZPIDinDBNotInAPI_FORSALE, EmailCustomersIfInterested
import base64

save_image_bp = Blueprint('save_image_bp', __name__, url_prefix='/picture')
from datetime import datetime


@save_image_bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@save_image_bp.route('/save_map_image', methods=['POST'])
def save_map_image():
    try:
        data = request.json['image']
        img_data = data.split(",")[1]  # Remove the "data:image/png;base64," part
        img_bytes = base64.b64decode(img_data)

        filename = f"app/static/map_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(filename, "wb") as f:
            f.write(img_bytes)

        return jsonify({"message": "Image saved successfully!", "filename": filename})

    except Exception as e:
        return jsonify({"error": str(e)}), 500