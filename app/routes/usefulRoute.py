# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE
# from flask import Flask, render_template, make_response
# from weasyprint import HTML
from app.MapTools.MappingTools import WA_geojson_features
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.RouteModel.AIModel import AIModel
from app.DBFunc.AIListingController import ailistingcontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO, SearchZillowHomesByLocation
from datetime import datetime
from app.RouteModel.BriefListingsVsApi import ZPIDinDBNotInAPI_FORSALE, EmailCustomersIfInterested
import os
useful_bp = Blueprint('useful_bp', __name__, url_prefix='/useful')
UPLOAD_FOLDER = 'static/maps'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@useful_bp.route('/upload-map', methods=['POST'])
def upload_map():
    file = request.files.get('file')
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({"status": "success", "path": filepath}), 200
    return jsonify({"status": "fail", "error": "No file"}), 400