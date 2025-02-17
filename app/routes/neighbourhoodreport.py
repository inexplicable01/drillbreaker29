# email_bp.py

from flask import Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.NeighbourhoodReport import NeighbourhoodReportDetails
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun

neighbourhoodreport_bp = Blueprint('neighbourhoodreport', __name__, url_prefix='/neighbourhoodreport')

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
neighbourhoods = ['Alki','Genesee','Seattle','Ravenna','Wallingford']

neighbourhoods = [
        'Shoreline', 'Bothell', 'Kenmore', 'Kirkland', 'Woodinville', 'Duvall', 'Carnation',
        'Auburn', 'Bellevue', 'Black Diamond', 'Burien', 'Clyde Hill', 'Covington', 'Des Moines', 'Enumclaw',
        'Federal Way', 'Hunts Point', 'Issaquah', 'Kenmore', 'Kent', 'Kirkland', 'Lake Forest Park', 'Maple Valley',
        'Medina', 'Mercer Island', 'Milton', 'Newcastle', 'Normandy Park', 'North Bend', 'Pacific', 'Redmond',
        'Renton', 'Sammamish', 'SeaTac', 'Seattle', 'Skykomish', 'Snoqualmie', 'Tukwila',
        'Yarrow Point'
    ]
@neighbourhoodreport_bp.route('/neighbourhood', methods=['GET','POST'])
def neigh_report():
    # neighbourhoods = brieflistingcontroller.uniqueNeighbourhood('Seattle')

    neighdata=[]
    for neighbourhood in neighbourhoods:
        averageprice,housesoldpriceaverage, map= NeighbourhoodReportDetails(neighbourhood, daysOfInterest=365*3)
        if housesoldpriceaverage=={}:
            continue
        neighdata.append(
            (neighbourhood,averageprice,housesoldpriceaverage, map)
        )
    return render_template('NeighbourhoodReport.html', neighdata=neighdata)




