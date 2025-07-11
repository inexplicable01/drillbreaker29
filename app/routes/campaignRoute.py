# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE
from app.DBFunc.CustomerTypeController import customertypecontroller
from app.RouteModel.AreaReportModel import AreaReportModelRun,AreaReportModelRunForSale, StatsModelRun
from app.RouteModel.EmailModel import sendLevel1BuyerEmail, sendunsubscribemeail,sendLevel3BuyerEmail , sendLevel1_2SellerEmail , sendpastcustomerEmail
from app.RouteModel.AreaReportModel import gatherCustomerData
# from app.RouteModel.AIModel import AIModel
# from app.DBFunc.AIListingController import ailistingcontroller
# from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
# from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
#     loadPropertyDataFromBrief, ListingStatus
from datetime import datetime, timedelta
from app.DBFunc.CustomerController import customercontroller
import re
from app.MapTools.MappingTools import create_map , WA_geojson_features
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO
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
base = "https://www.drillbreaker29.com/"

@campaignRoute_bp.route('/sendLevel1Buyer_sendEmail', methods=['GET'])
def sendLevel1Buyer_sendEmail():
    forreal =  request.json.get("forreal", False)
    level1_type = customertypecontroller.get_customer_type_by_id(1)
    level2_type = customertypecontroller.get_customer_type_by_id(3)

    level1_2_seller_customers = level1_type.customers+level2_type.customers

    next_thursday = get_next_thursday().strftime('%Y-%m-%d')
    customernames = []
    invalid_emails = []
    uniquecities = washingtoncitiescontroller.get_city_names_for_level1or2_buyers()
    output_dir = Path("app/static/maps")
    for customer in level1_2_seller_customers:
        if customer.dontemail:
            continue
        print(customer.name)
        customernames.append(customer.name)
        mappng = f"{base}static/maps/citymap_{customer.maincity.City}_{next_thursday}.png"
        pricechangepng = f"{base}static/maps/pricechange_{customer.maincity.City}_{next_thursday}.png"
        if not is_valid_email(customer.email):
            invalid_emails.append({'name': customer.name, 'email': customer.email})
            continue
        wcity = washingtoncitiescontroller.getCity(customer.maincity.City)
        if wcity:
            results = washingtonzonescontroller.getZoneListbyCity_id(wcity.city_id)
        else:
            results = washingtonzonescontroller.getzonebyName(customer.maincity.City)
        zone_ids = []
        for result in results:
            zone_ids.append(result.id)

        forsalehomes = brieflistingcontroller.get_recent_listings(customer, zone_ids)
        stats = StatsModelRun(zone_ids, 30)
        print(stats)
        sendLevel1BuyerEmail(customer, mappng , pricechangepng, forsalehomes, stats, forreal)
        # print(f"Prepared email for {customer.email} with images: {mappng}")

    return jsonify({
        'status': 'success',
        'customers': customernames,
        'invalid_emails': invalid_emails,
        'next_report_date': next_thursday,
        'uniquecities':uniquecities
    }), 200
import requests


@campaignRoute_bp.route('/sendLevel1Buyer_makepictures', methods=['POST'])
def sendLevel1Buyer_makepictures():
    next_thursday = get_next_thursday().strftime('%Y-%m-%d')
    customernames = []
    invalid_emails = []
    uniquecities = washingtoncitiescontroller.get_city_names_for_level1or2_buyers()
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


        url = f'{base}useful/upload-map'
        createPriceChangevsDays2PendingPlot(soldhomes,pricechangepng)
        with open(pricechangepng, 'rb') as f:
            files = {'file': (f'pricechange_{city}_{next_thursday}.png', f, 'image/png')}
            response = requests.post(url, files=files)
            print(response)

        create_map(WA_geojson_features, zonenames, map_html_path,mapname, soldhomes)
        with open(mapname, 'rb') as f:
            files = {'file': (f'citymap_{city}_{next_thursday}.png', f, 'image/png')}
            response = requests.post(url, files=files)
            print(response)

    return jsonify({
        'status': 'success',
        'customers': customernames,
        'invalid_emails': invalid_emails,
        'next_report_date': next_thursday,
        'uniquecities':uniquecities
    }), 200


@campaignRoute_bp.route('/sendLevel1_2_Seller_sendEmail', methods=['GET'])
def sendLevel1_2_Seller_sendEmail():
    forreal =  request.json.get("forreal", False)
    level1_seller = customertypecontroller.get_customer_type_by_id(2)
    level2_seller = customertypecontroller.get_customer_type_by_id(4)
    level3_seller = customertypecontroller.get_customer_type_by_id(6)
    level1_2_seller_customers = level1_seller.customers+level2_seller.customers+level3_seller.customers
    next_thursday = get_next_thursday().strftime('%Y-%m-%d')
    customernames = []
    invalid_emails = []
    uniquecities = washingtoncitiescontroller.get_city_names_for_level1or2_sellers()
    output_dir = Path("app/static/maps")
    for customer in level1_2_seller_customers:
        if customer.dontemail:
            continue
        print(customer.name)
        customernames.append(customer.name)
        # mappng = f"{base}static/maps/citymap_{customer.maincity.City}_{next_thursday}.png"
        # pricechangepng = f"{base}static/maps/pricechange_{customer.maincity.City}_{next_thursday}.png"
        if not is_valid_email(customer.email):
            invalid_emails.append({'name': customer.name, 'email': customer.email})
            continue
        wcity = washingtoncitiescontroller.getCity(customer.maincity.City)
        if wcity:
            results = washingtonzonescontroller.getZoneListbyCity_id(wcity.city_id)
        else:
            results = washingtonzonescontroller.getzonebyName(customer.maincity.City)
        zone_ids = []
        for result in results:
            zone_ids.append(result.id)

        soldhomes = brieflistingcontroller.get_recent_listings(customer, zone_ids, homestatus=RECENTLYSOLD)
        stats = StatsModelRun(zone_ids, 30 , 7)
        print(stats)
        sendLevel1_2SellerEmail(customer,  soldhomes, stats, forreal)
        # print(f"Prepared email for {customer.email} with images: {mappng}")

    return jsonify({
        'status': 'success',
        'customers': customernames,
        'invalid_emails': invalid_emails,
        'next_report_date': next_thursday,
        'uniquecities':uniquecities
    }), 200



@campaignRoute_bp.route('/sendLevel3Buyer_sendEmail', methods=['GET'])
def sendLevel3Buyer_sendEmail():
    # Query the customer and their interests
    forreal =  request.json.get("forreal", False)
    level3buyer_type = customertypecontroller.get_customer_type_by_id(5)

    for customer in level3buyer_type.customers:
        if customer.dontemail:
            continue

        (customer, locations, locationzonenames, customerlistings,
         housesoldpriceaverage, plot_url, plot_url2,
         soldhomes, forsalehomes_dict,
         brieflistings_SoldHomes_dict, selectedaicomments, ai_comment_zpid)  = gatherCustomerData(customer.id, 30)

        if not customer:
            return "No customers found", 404
        zones_ids = [zone.id for zone in customer.zones]
        stats = StatsModelRun(zones_ids, 30)
        sendLevel3BuyerEmail(customer,locations, plot_url, soldhomes, selectedaicomments, stats, forreal)

    # Redirect back to the same interests page after sending email
    return jsonify({
        'status': 'success',
    }), 200

@campaignRoute_bp.route('/pastcustomer_sendEmail', methods=['GET'])
def pastcustomer_sendEmail():
    # Query the customer and their interests
    forreal =  request.json.get("forreal", False)
    pastbuyer_type = customertypecontroller.get_customer_type_by_id(7)
    pastsellers_type = customertypecontroller.get_customer_type_by_id(8)
    pastcustomers = pastbuyer_type.customers + pastsellers_type.customers
    ##We should add some sort of service to this.
    for customer in pastcustomers:
        if customer.dontemail:
            continue
        # (customer, locations, locationzonenames, customerlistings,
        #  housesoldpriceaverage, plot_url, plot_url2,
        #  soldhomes, forsalehomes_dict,
        #  brieflistings_SoldHomes_dict, selectedaicomments, ai_comment_zpid)  = gatherCustomerData(customer.id, 30)
        # if not customer:
        #     return "No customers found", 404
        # zones_ids = [zone.id for zone in customer.zones]
        # stats = StatsModelRun(zones_ids, 30)
        sendpastcustomerEmail(customer, forreal)

    # Redirect back to the same interests page after sending email
    return jsonify({
        'status': 'success',
    }), 200


@campaignRoute_bp.route('/unsubscribe')
def unsubscribe():
    # Extract the email from the query string
    user_email = request.args.get('email')
    if not user_email:
        return "Missing email address", 400
    customer = customercontroller.getCustomerByEmail(user_email)
    sendunsubscribemeail(customer)
    # 3. Render or redirect to a simple confirmation page
    return render_template("unsubscribe_confirmed.html", email=user_email)
