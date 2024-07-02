# email_bp.py
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.NeighbourhoodReport import NeighbourhoodReportDetails

clickablemap_bp = Blueprint('clickablemap', __name__, url_prefix='/clickablemap')

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

@clickablemap_bp.route('/', methods=['GET','POST'])
def clickablemap():
    return render_template('ClickAbleMap.html')


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