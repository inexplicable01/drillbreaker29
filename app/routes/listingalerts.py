# email_bp.py
from flask import Blueprint, redirect, url_for
# from app.RouteModel.EmailModel import sendEmailwithListingforclient
# from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForForSaleHomes,loadPropertyDataFromBrief
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.RouteModel.EmailModel import SendEmailOfListings
from app.DBFunc.CustomerController import customercontroller

alert_bp = Blueprint('alerts', __name__, url_prefix='/listingalerts')


@alert_bp.route('/activeCustomers', methods=['GET'])
def activeCustomers():
    return {'activeCustomers':customercontroller.get_active_customers(as_dict=True)},200

# @alert_bp.route('/clientalerts', methods=['GET'])
# def sendalerts():
#     # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
#     clientinterest={
#         'area':['Judkins Park', 'Beacon Hill', 'North Beacon Hill',
#                 'Leschi', 'Central District','Atlantic','Mt Baker'],
#         'bedrooms_min':2,
#         'bedrooms_max': 3,
#         'bathrooms_min':1.5,
#         'pricemax': 700000
#     }
#     forsalebriefdata = ZillowSearchForForSaleHomes(clientinterest)
#     for brieflisting in forsalebriefdata:
#         try:
#             propertydata = loadPropertyDataFromBrief(brieflisting)
#             brieflisting.hdpUrl = propertydata['hdpUrl']
#         except Exception as e:
#             print(e, brieflisting)
#
#     changebrieflistingarr,oldbrieflistingarr=brieflistingcontroller.SaveBriefListingArr(forsalebriefdata)
#
#     for brieflisting in changebrieflistingarr:
#         print(brieflisting)
#     SendEmailOfListings(changebrieflistingarr,oldbrieflistingarr)
#
#     return redirect(url_for('main.index'))

