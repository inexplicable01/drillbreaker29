# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE
from app.DBFunc.CustomerTypeController import customertypecontroller
from app.RouteModel.AreaReportModel import AreaReportModelRun,AreaReportModelRunForSale
from app.RouteModel.EmailModel import sendLevel1Email
# from app.RouteModel.AIModel import AIModel
# from app.DBFunc.AIListingController import ailistingcontroller
# from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
# from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
#     loadPropertyDataFromBrief, ListingStatus
from datetime import datetime, timedelta
import re
from app.MapTools.MappingTools import create_map , WA_geojson_features
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO, SearchZillowHomesByLocation
from datetime import datetime
from app.RouteModel.BriefListingsVsApi import ZPIDinDBNotInAPI_FORSALE, EmailCustomersIfInterested
from app.GraphTools.plt_plots import *

campaignRoute_bp = Blueprint('campaignRoute_bp', __name__, url_prefix='/campaign')


def get_next_thursday():
    today = datetime.today()
    days_ahead = (3 - today.weekday()) % 7  # 3 = Thursday
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def is_valid_email(email):
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(regex, email) is not None

from pathlib import Path
import os

base = os.getenv("BASE")
@campaignRoute_bp.route('/sendLevel1Buyer', methods=['GET'])
def sendLevel1Buyer():
    level1_type = customertypecontroller.get_customer_type_by_id(1)

    ## Write a function here that creates  a list of cities that the level 1 customers care about .images of

    ## create a real estate report for each of those cities.  The report will basically be images stored on the server.
    ## the image names will be based on the nearest future thursday.  As these emails are supposed to only go out on thursdays.
    next_thursday = get_next_thursday().strftime('%Y-%m-%d')
    customernames = []
    invalid_emails = []
    uniquecities = washingtoncitiescontroller.get_city_names_for_level1_customers()
    output_dir = Path("app/static/maps")
    for city in uniquecities:
        # getzones....
        map_html_path = output_dir / f'citymap_{city}_{next_thursday}.html'
        mapname = output_dir / f'citymap_{city}_{next_thursday}.png'
        pricechangepng = output_dir / f'pricechange_{city}_{next_thursday}.png'
        wcity = washingtoncitiescontroller.getCity(city)
        if wcity:
            results = washingtonzonescontroller.getZoneListbyCity_id(wcity.city_id)
        else:
            results = washingtonzonescontroller.getzonebyName(city)

        zonenames=[]
        for result in results:
            zonenames.append(result.zonename())

        housesoldpriceaverage, soldhomes = AreaReportModelRun(zonenames,
                                                                                   [SW.TOWNHOUSE, SW.SINGLE_FAMILY],
                                                                                   30)
        createPriceChangevsDays2PendingPlot(soldhomes,pricechangepng)

        create_map(WA_geojson_features, zonenames, map_html_path,mapname, soldhomes)
        ## create the customer attention emails
    # cityname = washingtoncitiescontroller.get_city_name_by_id(city)
    ##Create Pictures for these cities
    #create the
    count = 0

    for customer in level1_type.customers:
        print(customer.name)
        customernames.append(customer.name)
        mappng = f"{base}/static/maps/citymap_{customer.maincity.City}_{next_thursday}.png"

        if not is_valid_email(customer.email):
            invalid_emails.append({'name': customer.name, 'email': customer.email})
            continue

        sendLevel1Email(customer, mappng)
        count += 1
        if count>4:
            break
        print(f"Prepared email for {customer.email} with images: {mappng}")

    return jsonify({
        'status': 'success',
        'customers': customernames,
        'invalid_emails': invalid_emails,
        'next_report_date': next_thursday,
        'uniquecities':uniquecities
    }), 200