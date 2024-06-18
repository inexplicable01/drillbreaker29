# email_bp.py
from flask import Blueprint, render_template, redirect, url_for
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.NeighbourhoodReport import NeighbourhoodReportDetails

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

@neighbourhoodreport_bp.route('/neighbourhood', methods=['GET','POST'])
def neigh_report():
    neighbourhoods = brieflistingcontroller.uniqueNeighbourhood('Seattle')
    neighdata=[]
    for neighbourhood in neighbourhoods:
        averageprice,housesoldpriceaverage, map= NeighbourhoodReportDetails(neighbourhood)
        if housesoldpriceaverage=={}:
            continue
        neighdata.append(
            (neighbourhood,averageprice,housesoldpriceaverage, map)
        )


    return render_template('NeighbourhoodReport.html', neighdata=neighdata)


