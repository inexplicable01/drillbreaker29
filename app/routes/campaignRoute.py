# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE
from app.DBFunc.CustomerTypeController import customertypecontroller
from app.RouteModel.AreaReportModel import AreaReportModelRun,AreaReportModelRunForSale, StatsModelRun
from app.RouteModel.EmailModel import (sendLevel1BuyerEmail, sendEmailtimecheck,
                                       sendunsubscribemeail,sendLevel3BuyerEmail , sendLevel1_2SellerEmail , sendpastcustomerEmail)
from app.RouteModel.AreaReportModel import gatherCustomerData
# from app.RouteModel.AIModel import AIModel
# from app.DBFunc.AIListingController import ailistingcontroller
# from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
# from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
#     loadPropertyDataFromBrief, ListingStatus
from datetime import datetime, timedelta
from app.DBFunc.CustomerController import customercontroller
from app.DBFunc.CadenceCommentController import commentcontroller
import re
# from app.MapTools.MappingTools import create_map , WA_geojson_features
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO
from datetime import datetime
from app.RouteModel.BriefListingsVsApi import ZPIDinDBNotInAPI_FORSALE, EmailCustomersIfInterested
from app.GraphTools.plt_plots import *
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller

campaignRoute_bp = Blueprint('campaignRoute_bp', __name__, url_prefix='/campaign')
defaultrecipient = 'waichak.luk@gmail.com'
mo_email = 'mohamedzabuzaid@gmail.com'

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

@campaignRoute_bp.route('/ping', methods=['GET'])
def ping_email():
    sendEmailtimecheck()
    return jsonify({
        'status': 'pinged',
    }), 200


@campaignRoute_bp.route('/sendLevel1Buyer_sendEmail', methods=['GET'])
def sendLevel1Buyer_sendEmail():
    emailtest=0
    forreal =  request.json.get("forreal", False)
    ignoretimerestriction = request.json.get("ignoretimerestriction", False)
    admin = request.json.get("admin", False)
    selectafew = request.json.get("selectafew", False)
    level1_type = customertypecontroller.get_customer_type_by_id(1)
    level2_type = customertypecontroller.get_customer_type_by_id(3)

    level1_2buyer_customers = level1_type.customers+level2_type.customers

    next_thursday = get_next_thursday().strftime('%Y-%m-%d')
    customernames = []
    invalid_emails = []
    uniquecities = washingtoncitiescontroller.get_city_names_for_level1or2_buyers()
    output_dir = Path("app/static/maps")
    for customer in level1_2buyer_customers:
        if customer.dontemail:
            continue
        print(customer.name)
        customernames.append(customer.name)
        mappng = f"{base}static/maps/citymap_{customer.maincity.City}_{next_thursday}.png"
        pricechangepng = f"{base}static/maps/pricechange_{customer.maincity.City}_{next_thursday}.png"
        if not is_valid_email(customer.email):
            invalid_emails.append({'name': customer.name, 'email': customer.email})
            continue

        if customercontroller.shouldsendEmail(customer) or ignoretimerestriction:

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

            emailsentsuccessfull = sendLevel1BuyerEmail(customer, pricechangepng, forsalehomes, stats, forreal, admin)


            if emailsentsuccessfull and forreal and not ignoretimerestriction:
                customercontroller.update_last_email_sent_at(customer)
                print(f"Email sent to {customer.email}; next due {customer.next_email_due_at:%Y-%m-%d %H:%M:%S}")
            elif emailsentsuccessfull and ignoretimerestriction:
                print(f"[TEST] Email sent to {defaultrecipient} (customer {customer.id} / {customer.email})")
            else:
                print(f"[FAIL] Email not sent for customer {customer.id} / {customer.email}")


        else:

            printoutEmailsThatWerentSent(customer)
        if selectafew:
            if emailtest >2:
                break
            emailtest+=1

    sendEmailtimecheck()
    return jsonify({
        'status': 'success',
        'customers': customernames,
        'invalid_emails': invalid_emails,
        'next_report_date': next_thursday,
        'uniquecities':uniquecities
    }), 200
import requests

def printoutEmailsThatWerentSent(customer):
    print("Not time to send email yet")  # Verbose skip diagnostics
    now = datetime.utcnow()
    cadence = int(customer.email_cadence_days or 14)
    last = customer.last_email_sent_at
    expected = (last + timedelta(days=cadence)) if last else customer.next_email_due_at
    next_due = customer.next_email_due_at or expected
    remaining = (next_due - now) if next_due else None

    def fmt_dt(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC") if dt else "—"

    def fmt_td(td):
        if td is None:
            return "—"
        secs = max(int(td.total_seconds()), 0)
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, _ = divmod(rem, 60)
        return f"{d}d {h}h {m}m"

    print(
        f"""
            [SKIP] Not time to send email yet.

            Customer
              ID: {customer.id}
              Name: {customer.name} {customer.lastname}
              Email: {customer.email}
              Phone: {customer.phone or '—'}
              Active: {bool(customer.active)}
              Paused: {bool(customer.paused)}
              Do-Not-Email: {bool(customer.dontemail)}
              Type ID: {customer.customer_type_id or '—'}
              Main City ID: {customer.maincity_id or '—'}

            Preferences
              Price Range: {customer.minprice}-{customer.maxprice} (Ideal: {customer.idealprice})
              Square Footage: {customer.minsqft}-{customer.maxsqft} (Ideal: {customer.idealsqft})
              Lot Size: {customer.lot_size or '—'}
              Parking Spaces Needed: {customer.parkingspaceneeded or '—'}

            Cadence / Timing
              Cadence (days): {cadence}
              Last Email Sent At: {fmt_dt(last)}
              Next Email Due At: {fmt_dt(next_due)}
              Time Until Next Send: {fmt_td(remaining)}
            """
    )






@campaignRoute_bp.route('/sendLevel1_2_Seller_sendEmail', methods=['GET'])
def sendLevel1_2_Seller_sendEmail():
    emailtest=0
    forreal =  request.json.get("forreal", False)
    ignoretimerestriction = request.json.get("ignoretimerestriction", False)
    admin = request.json.get("admin", False)
    selectafew = request.json.get("selectafew", False)
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
        # print(customer.name)
        customernames.append(customer.name)
        # mappng = f"{base}static/maps/citymap_{customer.maincity.City}_{next_thursday}.png"
        # pricechangepng = f"{base}static/maps/pricechange_{customer.maincity.City}_{next_thursday}.png"
        if customercontroller.shouldsendEmail(customer) or ignoretimerestriction:
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
            stats = StatsModelRun(zone_ids, customer.email_cadence_days , 7)
            # print(stats)
            emailsentsuccessfull =sendLevel1_2SellerEmail(customer,  soldhomes, stats, forreal)

            if emailsentsuccessfull and forreal and not ignoretimerestriction:
                customercontroller.update_last_email_sent_at(customer)
                print(f"Email sent to {customer.email}; next due {customer.next_email_due_at:%Y-%m-%d %H:%M:%S}")
            elif emailsentsuccessfull and ignoretimerestriction:
                print(f"[TEST] Email sent to {defaultrecipient} (customer {customer.id} / {customer.email})")
            else:
                print(f"[FAIL] Email not sent for customer {customer.id} / {customer.email}")
        # print(f"Prepared email for {customer.email} with images: {mappng}")
            if selectafew:
                if emailtest >2:
                    break
                emailtest+=1

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
        WA_geojson_features = washingtonzonescontroller.getallGeoJson()
        sendLevel3BuyerEmail(customer,locations,
                             plot_url, soldhomes,
                             selectedaicomments, stats,
                             WA_geojson_features, forreal)

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


def get_dummy_metrics(group: int) -> dict:
    # group: 1=cold buyers, 2=hot buyers, 3=sellers
    base = {
        "market_snapshot": {
            "median_price": "$725,000",
            "price_per_sqft": "$525",
            "days_on_market": 18,
            "inventory_mom": "+3%",
        },
        "rates": {"30yr_fixed": "6.6%", "5/6 ARM": "5.9%"},
    }
    if group == 1:  # cold buyers
        base["handpicked"] = [
            {"addr": "Tacoma – Lincoln Dist.", "price": "$489k", "beds": 3, "baths": 1.75, "link": "#"},
            {"addr": "Burien – Lakeview",      "price": "$615k", "beds": 3, "baths": 2.0,  "link": "#"},
        ]
        base["protip"] = "Reply with 'update my prefs' and your ideal price/area; I’ll re-target listings within 24h."
    elif group == 2:  # hot buyers
        base["handpicked"] = [
            {"addr": "West Seattle – Gatewood", "price": "$799k", "beds": 3, "baths": 2.25, "link": "#"},
            {"addr": "Shoreline – Meridian Pk", "price": "$735k", "beds": 4, "baths": 2.0,  "link": "#"},
        ]
        base["protip"] = "We can beat similar offers with a seller-paid buydown; ask me for a 1-page scenario."
    else:  # sellers
        base["seller_stats"] = {
            "buyer_traffic_wow": "+4%",
            "avg_list_to_sale": "98.5%",
            "new_listings_in_zip": 12,
        }
        base["protip"] = "Two low-lift wins: front entry refresh + scent-neutral clean. Converts more showings to offers."
    return base

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


# @campaignRoute_bp.route('/sendLevel1Buyer_makepictures', methods=['POST'])
# def sendLevel1Buyer_makepictures():
#     next_thursday = get_next_thursday().strftime('%Y-%m-%d')
#     customernames = []
#     invalid_emails = []
#     uniquecities = washingtoncitiescontroller.get_city_names_for_level1or2_buyers()
#     output_dir = Path("app/static/maps")
#     for city in uniquecities:
#         # getzones....
#         map_html_path = output_dir / f'citymap_{city}_{next_thursday}.html'
#         mapname = output_dir / f'citymap_{city}_{next_thursday}.png'
#         pricechangepng = output_dir / f'pricechange_{city}_{next_thursday}.png'
#         wcity = washingtoncitiescontroller.getCity(city)
#         if wcity:
#             results = washingtonzonescontroller.getZoneListbyCity_id(wcity.city_id)
#         else:
#             results = washingtonzonescontroller.getzonebyName(city)
#
#         zonenames=[]
#         for result in results:
#             zonenames.append(result.zonename())
#         housesoldpriceaverage, soldhomes = AreaReportModelRun(zonenames,
#                                              [SW.TOWNHOUSE, SW.SINGLE_FAMILY],
#                                                             30)
#
#
#         url = f'{base}useful/upload-map'
#         createPriceChangevsDays2PendingPlot(soldhomes,pricechangepng)
#         with open(pricechangepng, 'rb') as f:
#             files = {'file': (f'pricechange_{city}_{next_thursday}.png', f, 'image/png')}
#             response = requests.post(url, files=files)
#             print(response)
#
#         create_map(WA_geojson_features, zonenames, map_html_path,mapname, soldhomes)
#         with open(mapname, 'rb') as f:
#             files = {'file': (f'citymap_{city}_{next_thursday}.png', f, 'image/png')}
#             response = requests.post(url, files=files)
#             print(response)
#
#     return jsonify({
#         'status': 'success',
#         'customers': customernames,
#         'invalid_emails': invalid_emails,
#         'next_report_date': next_thursday,
#         'uniquecities':uniquecities
#     }), 200
