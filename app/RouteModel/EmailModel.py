import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from run import app
import os
from flask import render_template, flash
from app.config import Config
from app.NewListing import NewListing,NewListingForEmail
from app.EmailHelper.EmailSender import send_email , send_emailforOpenHouse
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBModels.BriefListing import BriefListing
from app.DBFunc.CustomerController import Customer, customercontroller
from app.DBFunc.CadenceCommentController import commentcontroller as CC
import pytz
from datetime import datetime, timedelta
from app.MapTools.MappingTools import WA_geojson_features
from flask_mail import Mail, Message
from jinja2 import Environment, FileSystemLoader

# from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForForSaleHomes,
defaultrecipient = 'waichak.luk@gmail.com'
mo_email = 'mohamedzabuzaid@gmail.com'
def sendEmailwithNewListing():
    # subject, body, recipient = defaultrecipient, html_content = None
    html_content = NewListingForEmail('Seattle', 1)
    # html_content=''
    send_email(subject='NewListing',
               html_content=html_content,
               recipient =defaultrecipient)

def sendEmailtimecheck(message=None):
    # subject, body, recipient = defaultrecipient, html_content = None
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')

    # Prepare the email content
    html_content = f"""
    <html>
        <body>
            <p>The email was sent on {formatted_time} (Seattle Time).</p>
            <p>Here is the rest of your email content.</p>
            <p>{message}</p>
        </body>
    </html>
    """
    # html_content=''
    send_email(subject='NewListing',
               html_content=html_content,
               recipient =defaultrecipient)

def sendEmailListingChange(message=None, title=None, hdpUrl=None):
    # subject, body, recipient = defaultrecipient, html_content = None
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')

    # Prepare the email content
    html_content = f"""
    <html>
        <body>
            <p>The email was sent on {formatted_time} (Seattle Time).</p>
            <p>{message}</p>
            <a href='https://www.zillow.com{hdpUrl}' target='_blank'>House Link</a>
        </body>
    </html>
    """
    # html_content=''

    send_email(subject=title,
               html_content=html_content,
               recipient =defaultrecipient)


def sendEmailListingChange(message=None, title=None, hdpUrl=None):
    # subject, body, recipient = defaultrecipient, html_content = None
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')

    # Prepare the email content
    html_content = f"""
    <html>
        <body>
            <p>The email was sent on {formatted_time} (Seattle Time).</p>
            <p>{message}</p>
            <a href='https://www.zillow.com{hdpUrl}' target='_blank'>House Link</a>
        </body>
    </html>
    """
    # html_content=''

    send_email(subject=title,
               html_content=html_content,
               recipient =defaultrecipient)

from pathlib import Path
def sendemailforcustomerhometour(customer:Customer,brieflisting):
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')


    email_subject = f"Customer {customer.name} , {customer.id} wants to tour {brieflisting.__str__()}!"
    # Prepare the email content
    html_content = f"""
    <html>
        <body>
            <p>The email was sent on {formatted_time} (Seattle Time).</p>
            <p>{email_subject}</p>
            <a href='https://www.zillow.com{brieflisting.hdpUrl}' target='_blank'>House Link</a>
        </body>
    </html>
    """

    try:
        send_email(
            subject=email_subject,
            recipient='waichak.luk@gmail.com',#customer.email,  # Email address of the customer
            html_content=html_content
        )
        send_email(
            subject=email_subject,
            recipient='mohamedzabuzaid@gmail.com',#customer.email,  # Email address of the customer
            html_content=html_content
        )
        flash("The email was sent successfully!", "success")
    except Exception as e:
        print(f"Error sending email: {e}")
        flash("An error occurred while sending the email.", "danger")




def sendEmailpending():
    # Define Seattle timezone
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')

    # Fetch all city statistics
    citiesdata = zonestatscachecontroller.get_all_zone_stats()

    # Prepare city statistics for the template
    zone_stats = [
        {
            "city_name": citydata.city_name,
            "sold": citydata.sold,
            "pending": citydata.pending,
            "forsale": citydata.forsale,
            "updated_time": (
                citydata.updated_time.astimezone(seattle_tz).strftime('%m/%d/%Y %I:%M %p %A')
                if citydata.updated_time
                else "N/A"
            )
        }
        for citydata in citiesdata
    ]

    # Initialize a dictionary to hold listings for each city of interest
    cityofinterest = ['Seattle', 'Bellevue', 'Kirkland']
    listings_data = {city: [] for city in cityofinterest}

    # Fetch pending listings for each city of interest
    for cityname in cityofinterest:
        listings = brieflistingcontroller.pendingListingsByCity(cityname, 1)  # Assuming '1' signifies last day
        for listing in listings:
            if isinstance(listing, BriefListing):
                listings_data[cityname].append(listing.to_dict())

    html_content = render_template(
        'Email_PendingTemplate.html',  # Your template in app/templates
        formatted_time=formatted_time,
        zone_stats=zone_stats,
        listings_data=listings_data
    )

    # Send the email
    send_email(
        subject='Pending Listings',
        html_content=html_content,
        recipient=defaultrecipient
    )

def bareboneshtmlcontent(customer):
    html_content = f"""
    <html>
        <body>
            <p>{customer.name}</p>
        </body>
    </html>
    """
    return html_content
from typing import List, Dict, Any, Tuple
def _history_html(history: List[Dict[str, Any]]) -> str:
    if not history:
        return "<p><em>No prior notes—this may be your first touch.</em></p>"
    items = "".join(
        f"<li><strong>{h.get('when','')}</strong> [{h.get('tag','')}] – {h.get('text','')}</li>"
        for h in history
    )
    return f"<ul>{items}</ul>"

def build_email_content(
    customer,
    group: int,
    history: List[Dict[str, Any]],
    data: Dict[str, Any],
) -> Tuple[str, str]:

    name = customer.name or "there"
    snap = data.get("market_snapshot", {})
    rates = data.get("rates", {})
    hist = _history_html(history)

    if group == 1:  # cold buyers
        cards = "".join([f"<li>{x['addr']} — {x['price']} • {x['beds']}bd/{x['baths']}ba <a href='{x['link']}'>View</a></li>"
                         for x in data.get("handpicked", [])])
        subject = f"{name}, quick picks & market snapshot"
        html = f"""
        <h3>Hi {name}, here are two quick picks</h3>
        <ul>{cards}</ul>
        <p><strong>Market snapshot:</strong> Median {snap.get('median_price')}, {snap.get('price_per_sqft')} /sqft, DOM {snap.get('days_on_market')}.</p>
        <p><strong>Rates:</strong> 30y {rates.get('30yr_fixed')}, 5/6 ARM {rates.get('5/6 ARM')}.</p>
        <p><em>Pro tip:</em> {data.get('protip','')}</p>
        <hr><h4>Your recent history</h4>{hist}
        """
    elif group == 2:  # hot buyers
        cards = "".join([f"<li>{x['addr']} — {x['price']} • {x['beds']}bd/{x['baths']}ba <a href='{x['link']}'>Tour?</a></li>"
                         for x in data.get("handpicked", [])])
        subject = f"{name}, new tour options & offer edge"
        html = f"""
        <h3>Tour-ready homes</h3>
        <ul>{cards}</ul>
        <p><strong>Tactical edge:</strong> Seller-paid buydown can cut payment ~$250–$450/mo—ask for your 1-pager.</p>
        <p><strong>Market:</strong> DOM {snap.get('days_on_market')}, inv MoM {snap.get('inventory_mom')}.</p>
        <hr><h4>Your recent history</h4>{hist}
        """
    else:  # sellers
        s = data.get("seller_stats", {})
        subject = f"{name}, this week’s prep & pricing signals"
        html = f"""
        <h3>Seller signals</h3>
        <ul>
          <li>Buyer traffic WoW: {s.get('buyer_traffic_wow')}</li>
          <li>Avg list-to-sale: {s.get('avg_list_to_sale')}</li>
          <li>New listings in ZIP: {s.get('new_listings_in_zip')}</li>
        </ul>
        <p><strong>Market snapshot:</strong> Median {snap.get('median_price')}, {snap.get('price_per_sqft')} /sqft.</p>
        <p><em>Prep tip:</em> {data.get('protip','')}</p>
        <hr><h4>Your recent history</h4>{hist}
        """
    return subject, html

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

from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller

def EmailOutToLeads(data , test, group):
    ##  So lets try doing this with one of each type Level 1 Buyer
    # LEvel 2 buyer
    # Level 3 seller
    ## Start with level 3 Buyers Start with a cadence

    customer = customercontroller.getCustomerByID(data["id"])







def SendEmailOfListings(changebrieflistingarr,oldbrieflistingarr):
    # subject, body, recipient = defaultrecipient, html_content = None
    neworupdatedlistings = []
    pastlistings=[]

    for infodump, arr in [(neworupdatedlistings,changebrieflistingarr), (pastlistings,oldbrieflistingarr)]:

        for brieflisting in arr:
            images=[]
            count = 0
            listingdetails = loadPropertyDataFromBrief(brieflisting)
            if not listingdetails:
                continue
            try:
                if listingdetails['address']['city']!='Seattle':
                    continue
                # print(listingdetails['address']['streetAddress'], listingdetails['address']['city'])

                for photo in listingdetails['photos']:
                    for jpeg in photo['mixedSources']['jpeg']:
                        if jpeg['width']==384:
                            images.append({
                                "url": jpeg['url'], "caption": photo['caption']
                            })
                            count = count +1
                    if count>2:
                        break

                infodump.append(
                    (listingdetails,f"{brieflisting.zpid}",images,brieflisting.zillowapi_neighbourhood)
                )
            except Exception as e:
                print(e)

    html_content =  render_template('Email_House_List.html', neworupdatedlistings=neworupdatedlistings,
                                    pastlistings=pastlistings)
    # html_content=''
    send_email(subject='NewListing',
               html_content=html_content,
               recipient =defaultrecipient)


def sendAppointmentEmail(name,email,phone,viewing_date,viewing_time,zpid,address):
    # subject, body, recipient = defaultrecipient, html_content = None
    html_content = render_template('Email_Appointment.html', name=name,email=email,
                                   phone=phone,viewing_date=viewing_date,viewing_time=viewing_time,zpid=zpid,address=address)
    # html_content=''
    send_email(subject='New Appointment',
               html_content=html_content,
               recipient =defaultrecipient)

import random
def generate_weekly_summary(city_name, stats):
    options = [
        {
            "headline": f"Out of {stats['total_pending']} that went under contract this week, {stats['fast_sales']} homes sold in under a week.",
            "body": f"{stats['total_pending']} homes went pending in {city_name} this week. The market is moving fast — the quickest went pending in just {stats['fastest_days']} days."
        },
        {
            "headline": f"{stats['under_list']} homes sold under asking.",
            "body": f"Buyers found some deals this week. In {city_name}, {stats['under_list']} listings went pending below list price. Know where the bargains are — and when to move on them."
        },
        {
            "headline": f"Is {city_name} heating up or cooling down?",
            "body": f"Your area saw {stats['total_sold']} sales this week, with a median days-on-market of {stats['median_days']} days. Want to know where to jump in? That’s what we're here for."
        },
    ]
    return random.choice(options)

from datetime import date

def classify_market(m):
    dom = m["dom"]; sale_to_list = m["sale_to_list"]; over_ask = m["pct_over_ask"]
    if dom < 10 and (sale_to_list >= 100 or over_ask >= 30):
        return {"label": "HOT", "badge_bg": "#e74c3c"}       # red
    if 10 <= dom <= 20 and 99 <= sale_to_list <= 100:
        return {"label": "BALANCED", "badge_bg": "#f39c12"}  # amber
    return {"label": "COOL", "badge_bg": "#27ae60"}          # green

def _dir(curr, prev, thresh=0.02):
    d = (curr - prev)
    if d > thresh:  return "up"
    if d < -thresh: return "down"
    return "neutral"

def dummy_metrics():
    m = {
        "as_of": date.today().isoformat(),
        "rate": 6.60,      "rate_prev": 6.55,
        "dom": 14,         "dom_prev": 16,
        "sale_to_list": 101.2, "sale_to_list_prev": 100.8,
        "pct_under_7d": 42, "pct_price_cuts": 28, "pct_over_ask": 36,
        "arrow": "→",  # keep if you still use it elsewhere
    }
    m["rate_dir"] = _dir(m["rate"], m["rate_prev"])            # ↑ if rate rose
    m["dom_dir"]  = _dir(m["dom"], m["dom_prev"])              # ↑ if DOM rose
    m["comp_dir"] = _dir(m["sale_to_list"], m["sale_to_list_prev"])  # ↑ if sale→list rose
    return m



def sendLevel1BuyerEmail(customer, mappng, pricechangepng, forsalehomes, stats, forreal=False):
    # subject, body, recipient = defaultrecipient, html_content = None
    history = customercontroller.last_comments(customer.id, limit=3)
    group = 1
    subject, html_content2 = build_email_content(customer, 1, history, get_dummy_metrics(group))
    customercontroller.add_comment(customer.id, f"Emailed (group {group}): {subject}", tag="email")

    weekly_summary = generate_weekly_summary(customer.maincity.City, stats)
    data = get_dummy_metrics(group)
    snap = data.get("market_snapshot", {})
    rates = data.get("rates", {})
    hist = _history_html(history)
    metrics = dummy_metrics()

    CC.add_email_digest(customer.id, metrics)  # store today’s digest in CadenceComment
    ai_text = CC.generate_ai_explainer(customer, segment=customer.customer_type_id, current_metrics=metrics)

    html_content = render_template(
        'EmailCampaignTemplate/email_level1Buyer.html',  # Your template in app/templates
        customer=customer,
        mappng=mappng,
        pricechangepng=pricechangepng,
        weekly_summary=weekly_summary,
        snap=snap,
        rates=rates,
        hist=hist,
        data=data,
        ai_text= ai_text,
        stats=stats,
        forsalehomes=forsalehomes,
        metrics=metrics,
        showScheduleButton=True
    )

    if forreal:
        return send_email(subject=f'Wayber Real Estate Analytics : {customer.maincity.City}',
                   html_content=html_content,
                   recipient =customer.email)
    else:
        return send_email(subject=f'Wayber Real Estate Analytics : {customer.maincity.City}',
                   html_content=html_content,
                   recipient =defaultrecipient)
        # return send_email(subject=subject,
        #            html_content=html_content2,
        #            recipient =defaultrecipient)



        # send_email(subject=f'Wayber Real Estate Analytics : {customer.maincity.City}',
        #            html_content=html_content,
        #            recipient =mo_email)

def sendLevel3BuyerEmail(customer:Customer,locations,
                      plot_url, soldhomes, selectedaicomments,stats, forreal=False):


    weekly_summary = generate_weekly_summary(customer.maincity.City, stats)
    email_subject = f"{customer.name} Neighborhood Interests"
    email_html_content = render_template(
        'EmailCampaignTemplate/email_level3Buyer.html',
        weekly_summary=weekly_summary,
        customer=customer,
        stats=stats,
        locations=locations,
        geojson_features=WA_geojson_features,
        soldhouses=soldhomes,
        selectedaicomments=selectedaicomments
    )

    try:
        if forreal:
            send_email(
                subject=email_subject,
                recipient=customer.email,  # Email address of the customer
                html_content=email_html_content
            )
        else:
            send_email(
                subject=email_subject,
                recipient='waichak.luk@gmail.com',#customer.email,  # Email address of the customer
                html_content=email_html_content
            )
            send_email(
                subject=email_subject,
                recipient=mo_email,#customer.email,  # Email address of the customer
                html_content=email_html_content
            )
        flash("The email was sent successfully!", "success")
    except Exception as e:
        print(f"Error sending email: {e}")
        flash("An error occurred while sending the email.", "danger")

def sendLevel1_2SellerEmail(customer, soldhomes, stats,
                            forreal=False):

    email_subject = f'Wayber Real Estate Analytics : {customer.maincity.City}'
    weekly_summary = generate_weekly_summary(customer.maincity.City, stats)

    html_content = render_template(
        'EmailCampaignTemplate/email_sellercustomer.html',  # Your template in app/templates
        customer=customer,
        weekly_summary=weekly_summary,
        stats=stats,
        soldhomes=soldhomes,
        showScheduleButton=True,
        website='https://www.wayber.net/'
    )

    try:
        if forreal:
            send_email(
                subject=email_subject,
                recipient=customer.email,  # Email address of the customer
                html_content=html_content
            )
        else:
            send_email(
                subject=email_subject,
                recipient='waichak.luk@gmail.com',#customer.email,  # Email address of the customer
                html_content=html_content
            )
            send_email(
                subject=email_subject,
                recipient=mo_email,#customer.email,  # Email address of the customer
                html_content=html_content
            )
        flash("The email was sent successfully!", "success")
    except Exception as e:
        print(f"Error sending email: {e}")
        flash("An error occurred while sending the email.", "danger")

def sendpastcustomerEmail(customer:Customer, forreal=False):


    # weekly_summary = generate_weekly_summary(customer.maincity.City, stats)
    email_subject = f"{customer.name} Neighborhood Interests"
    email_html_content = render_template(
        'EmailCampaignTemplate/email_pastcustomer.html',
        customer = customer,
        website='https://www.wayber.net/'

    )

    try:
        if forreal:
            send_email(
                subject=email_subject,
                recipient=customer.email,  # Email address of the customer
                html_content=email_html_content
            )
        else:
            send_email(
                subject=email_subject,
                recipient='waichak.luk@gmail.com',#customer.email,  # Email address of the customer
                html_content=email_html_content
            )
        flash("The email was sent successfully!", "success")
    except Exception as e:
        print(f"Error sending email: {e}")
        flash("An error occurred while sending the email.", "danger")


def sendunsubscribemeail(customer):
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
        <h2 style="color: #c0392b;">Unsubscribe Request</h2>
        <p><strong>{customer.name}</strong> (<a href="mailto:{customer.email}">{customer.email}</a>) has requested to unsubscribe from Wayber emails.</p>

        <p style="margin-top: 20px;">No automated action has been taken. Please remove them manually from the list.</p>

        <p style="font-size: 12px; color: #888;">Customer ID: {customer.id}</p>
    </div>
    """

    send_email(
        subject=f'{customer.name} wants to unsubscribe',
        html_content=html_content,
        recipient=defaultrecipient
    )


from typing import Any, Dict, List, Tuple
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
REQUIRED_FIELDS = {"email"}

def _normalize_payload_from_request() -> Dict[str, Any]:
    """
    Accept JSON or form and normalize to a flat dict[str, str].
    Prefer JSON in clients. This keeps legacy form posts working.
    """
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            raise BadRequest("JSON body must be an object")
        flat = {k: "" if v is None else str(v) for k, v in data.items()}
    else:
        flat = request.form.to_dict(flat=True)

    missing = [k for k in REQUIRED_FIELDS if k not in flat or flat[k] == ""]
    if missing:
        raise BadRequest(f"Missing required fields: {', '.join(missing)}")
    return flat


def _normalize_batch_from_request() -> List[Dict[str, Any]]:
    """
    Expect JSON: { "customers": [ {...}, {...} ] }
    Also tolerates form with a single 'customers' JSON string.
    """
    body = {}
    if request.is_json:
        body = request.get_json(silent=True) or {}
    else:
        # allow form clients to send a JSON string under 'customers'
        import json
        if "customers" in request.form:
            try:
                body = {"customers": json.loads(request.form["customers"])}
            except Exception:
                raise BadRequest("Form field 'customers' must be JSON")

    customers = body.get("customers")
    if not isinstance(customers, list) or not customers:
        raise BadRequest("Body must include non-empty array 'customers'")

    normalized: List[Dict[str, Any]] = []
    for c in customers:
        if not isinstance(c, dict):
            raise BadRequest("Each customer must be an object")
        normalized.append({k: "" if v is None else str(v) for k, v in c.items()})
    return normalized


def _send_one(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Calls your existing email logic. Return (ok, message).
    """
    try:
        # Replace with your import if needed to avoid circulars
        EmailOutToLeads(payload)
        return True, "sent"
    except Exception as e:
        current_app.logger.exception(f"Email send failed: {e}")
        return False, f"failed: {e}"