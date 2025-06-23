from app.DBFunc.WashingtonZonesController import WashingtonZonesController, washingtonzonescontroller
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from flask import flash,Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,AreaReportModelRunForSale
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE, PENDING
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
dirty_scoop_bp = Blueprint('dirty_scoop_bp', __name__, url_prefix='/dirty_scoop')
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from app.DBFunc.AIListingController import ailistingcontroller
from app.DBFunc.CustomerController import customercontroller
from app.DBFunc.PropertyListingController import propertylistingcontroller
from app.MapTools.MappingTools import WA_geojson_features, create_map
from app.RouteModel.AIModel import AIModel
from app.RouteModel.EmailModel import sendemailforcustomerhometour
from app.DBFunc.CustomerZpidController import customerzpidcontroller
from app.ZillowAPI.ZillowAPICall import SearchZilowByMLSID, SearchZillowByZPID
import requests
from app.RouteModel.AreaReportModel import gatherCustomerData
from app.GraphTools.plt_plots import *
from geopy.geocoders import Nominatim

RAPIDAPI_KEY = "0bc02c9596msh137f931ca8f2502p12d190jsn7dd0bc9a97dc"
RAPIDAPI_HOST = "sex-offenders.p.rapidapi.com"

@dirty_scoop_bp.route('/', methods=['GET', 'POST'])
def index():
    offender_data = None
    error = None

    if request.method == 'POST':
        address = request.form.get('address')
        try:
            geolocator = Nominatim(user_agent="wayber_offender_lookup")
            location = geolocator.geocode(address)

            if not location:
                raise ValueError("Could not geocode address")

            lat = location.latitude
            lng = location.longitude

            querystring = {
                "lat": str(lat),
                "lng": str(lng),
                "radius": "0",  # Can be increased if you want to search a wider area
                "zipcode": address.split()[-1],  # crude zipcode attempt
                "mode": "extensive"
            }

            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }

            response = requests.get(f"https://{RAPIDAPI_HOST}/sexoffender", headers=headers, params=querystring)
            response.raise_for_status()
            offender_data = response.json().get('offenders', [])

        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template("DirtyScoop/DirtyScoop.html", offenders=offender_data, error=error)
