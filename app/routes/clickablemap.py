# email_bp.py
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.NeighbourhoodReport import NeighbourhoodReportDetails
import json
from shapely.geometry import Point, shape

clickablemap_bp = Blueprint('clickablemap_bp', __name__, url_prefix='/clickablemap')

# @email_bp.route('/send-test', methods=['POST'])
# def send_test_email():
#     # Use a subset of your listings or dummy data for testing
#     test_listings = [{'id': 1, 'details': 'Can you see this'},
#                      {'id': 2, 'details': 'tyjkhggg'}]
#
#     email_content = "New Listings:\n"
#     for listing in test_listings:
#         email_content += f"ID: {listing['id']}, Details: {listing['details']}\n"
#     # Assuming `send_email` is a function that actually sends the email.
#     # send_email('New Listing', email_content)
#     return redirect(url_for('main.index'))


# Load GeoJSON data once at app initialization
file_path = 'app/MapTools/Neighborhood_Map_Atlas_Neighborhoods.geojson'
with open(file_path, 'r') as f:
    geojson_data = json.load(f)
geojson_features = geojson_data['features']


def replace_none(obj):
    if isinstance(obj, list):
        return [replace_none(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: replace_none(v) for k, v in obj.items()}
    elif obj is None:
        return None  # Explicitly returning None to align with JSON `null`
    return obj


geojson_features = replace_none(geojson_data['features'])

# Create a Blueprint for the clickable map


def get_neighborhood(lat, lon, features):
    """Find the neighborhood for a given latitude and longitude."""
    point = Point(lon, lat)  # Shapely expects (lon, lat)
    for feature in features:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return feature['properties']['L_HOOD']  # Replace with desired property
    return None


@clickablemap_bp.route('/', methods=['GET','POST'])
def clickablemap():
    # geojson_features
    blah = list(range(0, 10))  # Convert range to a list

    # for g in geojson_features:
    #     g['properties']['S_HOOD_ALT_NAMES']='None'

    return render_template('ClickAbleMap.html', blah=blah,geojson_features=geojson_features)


@clickablemap_bp.route('/process', methods=['POST'])
def process():
    region = request.json.get('region')
    # Process data based on the region
    # For example, you can generate graphs or perform some calculations
    if region == 'Seattle':
        data = {'message': 'Data processed for Seattle'}
        # Here you can add code to generate graphs or other processed data
    elif region == 'Bellevue':
        data = {'message': 'Data processed for Bellevue'}
        # Here you can add code to generate graphs or other processed data
    else:
        data = {'message': 'Unknown region'}

    return jsonify(data)