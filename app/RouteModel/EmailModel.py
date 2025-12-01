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

from typing import Optional, Dict, Any, Tuple
from app.RouteModel.RatesModel import *
from app.RouteModel.StatsOrganizingMethods import *
from flask_mail import Mail, Message
from jinja2 import Environment, FileSystemLoader
from app.Models.Rates import *

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
            <p>{message}</p>
        </body>
    </html>
    """
    # html_content=''
    send_email(subject=message,
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


def sendEmailListingChange(message=None, title=None, hdpUrl=None, customer=None):
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%B %d, %Y at %I:%M %p %Z')

    message = message or ""
    message_html = "<br>".join(message.splitlines())

    customer_name = None
    customer_email = None

    if customer is not None:
        customer_name = getattr(customer, "name", None) or getattr(customer, "first_name", None)
        customer_email = customer.email or getattr(customer, "email_address", None)

    greeting_name = customer_name.split()[0] if customer_name else "there"
    recipient = customer_email or defaultrecipient

    listing_link_html = ""
    if hdpUrl:
        listing_link_html = f"""
            <div class="cta">
                <a href="https://www.zillow.com{hdpUrl}" target="_blank">
                    View this home on Zillow
                </a>
            </div>
        """

    html_content = f"""
    <html>
      <head>
        <meta charset="UTF-8" />
        <style>
          /* (same styles as before) */
        </style>
      </head>
      <body>
        <div class="wrapper">
          <div class="card">
            <div class="header">
              <p class="header-title">Home update from Wayber</p>
              <p class="subtext">Sent on {formatted_time} (Seattle time)</p>
            </div>

            <p class="greeting">Hi {greeting_name},</p>

            <p style="font-size:14px; margin: 0 0 12px 0;">
              There’s been an update to a home you’re following. Here are the details:
            </p>

            <div class="message-block">
              {message_html}
            </div>

            {listing_link_html}

            <p class="brand">
              Best regards,<br>
              Wayber Team
            </p>

            <p class="footer">
              You’re receiving this email because you asked Wayber to track this property for you.
              If you’d like to stop receiving updates for this home, simply reply to this email and let us know.
            </p>
          </div>
        </div>
      </body>
    </html>
    """
    # send_email(
    #     subject=title,
    #     html_content=html_content,
    #     recipient=customer_email
    # )
    send_email(
        subject=title,
        html_content=html_content,
        recipient='waichak.luk@gmail.com'
    )



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




def build_verdicts_from_ai(ai, mortgageoutlook):
    """
    ai: dict with ai['conclusions'] = {rates,speed,competition,price}
    returns: {'rates': str, 'speed': str, 'competition': str, 'price': str}
    """
    c = (ai or {}).get("conclusions") or {}
    return {
        "rates":       verdict_sentence("rates",       mortgageoutlook['30y_fixed']['direction']),
        "speed":       verdict_sentence("speed",       c.get("speed")),
        "competition": verdict_sentence("competition", c.get("competition")),
        "sold_price":       verdict_sentence("sold_price",       c.get("sold_price")),
    }

import pandas as pd
def sendLevel1BuyerEmail(customer, pricechangepng, forsalehomes, stats, forreal=False, admin=False):
    ai_history = CC.recent_cadences(customer.id, limit=5)
    weekly_summary = generate_weekly_summary(customer.maincity.City, stats)

    m30 = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US",
                      parse_dates=["observation_date"]).set_index("observation_date")["MORTGAGE30US"].resample("W-THU").last().dropna()
    m15 = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE15US",
                      parse_dates=["observation_date"]).set_index("observation_date")["MORTGAGE15US"].resample("W-THU").last().dropna()
    history = {
        "30y_fixed": m30.tail(16).tolist(),
        "15y_fixed": m15.tail(16).tolist(),
        # "5_1_arm": obmmi.tail(16).tolist(),  # when you have it
        # "20y_fixed": [...]  # optional; else we approximate between 15y/30y
    }
    mortgageoutlook = mortgage_rate_outlook(history, weeks_ahead=4)

    metrics = verbalize_stats(stats or {}, customer.email_cadence_days)

    try:
        ai = CC.generate_ai_explainer_structured_from_stats(
            customer=customer,
            segment=customer.customer_type_id,
            stats = stats,
            metrics=metrics,
        )
        # CC.add_email_digest(customer.id, metrics)
    except Exception:
        ai = None
    labels = derive_header_fields(stats, ai)
    meeting_url = "https://www.drillbreaker29.com/meet?customer_id={}".format(customer.id)

    verdicts = build_verdicts_from_ai(ai,mortgageoutlook)

    ##Select only quality listings
    ##TODO Use AI to tailer choose listings for email.
    displaylistings = []
    for listings in forsalehomes:
        if listings.price>1000:
            displaylistings.append(listings)
        if len(displaylistings)>3:
            break

    html_content = render_template(
        'EmailCampaignTemplate/email_level1Buyer.html',
        customer=customer,
        weekly_summary=weekly_summary,
        # snap=snap,
        # rates=rates,
        # hist=hist,
        data={},
        ai=ai,
        verdicts=verdicts,
        meeting_url=meeting_url,
        stats=stats,
        forsalehomes=displaylistings,
        metrics=metrics,
        admin=admin,
        ai_history=ai_history,
        labels=labels,
        mortgageoutlook=mortgageoutlook
    )

    # subject_rate = "{:.2f}%".format(metrics["rate"]) if isinstance(metrics.get("rate"), (int, float)) else str(metrics.get("rate"))
    # subject_dom = snap["days_on_market"]
    # subject = "Wayber • {}: rates {} · DOM {}".format(customer.maincity.City, subject_rate, subject_dom)


    if forreal:
        recipient = customer.email
    else:
        recipient = defaultrecipient

    if admin:
        recipient = defaultrecipient


    return send_email(subject=f'{ai["title"]}',
               html_content=html_content,
               recipient =recipient)
        # return send_email(subject=subject,
        #            html_content=html_content2,
        #            recipient =defaultrecipient)



        # send_email(subject=f'Wayber Real Estate Analytics : {customer.maincity.City}',
        #            html_content=html_content,
        #            recipient =mo_email)

def sendLevel3BuyerEmail(customer:Customer,locations,
                      plot_url, soldhomes, selectedaicomments,stats, WA_geojson_features,forreal=False):


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

def sendLevel2SellerEmailWithAnalysis(customer, soldhomes, stats, analysis_result=None,
                                     forreal=False, admin=False):
    """
    Send email to Level 2 sellers with property-specific regression analysis.
    """
    ai_history = CC.recent_cadences(customer.id, limit=5)
    metrics = verbalize_stats(stats or {}, customer.email_cadence_days)

    email_subject = f'Wayber Real Estate Analytics : {customer.maincity.City}'
    weekly_summary = generate_weekly_summary(customer.maincity.City, stats)

    try:
        ai = CC.generate_ai_explainer_structured_from_stats(
            customer=customer,
            segment=3,
            stats=stats,
            metrics=metrics,
        )
    except Exception:
        ai = None

    verdicts = {
        "sold_price": verdict_sentence("sold_price", ai['conclusions']['sold_price']),
        "speed": verdict_sentence("speed", ai['conclusions']['speed']),
        "inventory": verdict_sentence("competition", ai['conclusions']['inventory']),
    }
    labels = derive_header_fields(stats, ai)

    # Render template with analysis data
    html_content = render_template(
        'EmailCampaignTemplate/email_level2seller_analysis.html',
        customer=customer,
        weekly_summary=weekly_summary,
        ai_history=ai_history,
        ai=ai,
        stats=stats,
        verdicts=verdicts,
        soldhomes=soldhomes,
        analysis=analysis_result,  # NEW: Analysis results
        showScheduleButton=True,
        website='https://www.wayber.net/',
        labels=labels
    )

    try:
        if forreal:
            send_email(subject=f'{ai["title"]}- copy sent to Customer',
                       html_content=html_content,
                       recipient=defaultrecipient)

            recipient = customer.email
        else:
            recipient = defaultrecipient
        return send_email(subject=f'{ai["title"]}',
                          html_content=html_content,
                          recipient=recipient)

    except Exception as e:
        print(f"Error sending email: {e}")
        flash("An error occurred while sending the email.", "danger")


def sendLevel1_2SellerEmail(customer, soldhomes, stats,
                            forreal=False, admin=False):

    ai_history = CC.recent_cadences(customer.id,  limit=5)

    metrics = verbalize_stats(stats or {}, customer.email_cadence_days)

    email_subject = f'Wayber Real Estate Analytics : {customer.maincity.City}'
    weekly_summary = generate_weekly_summary(customer.maincity.City, stats)

    try:
        ai = CC.generate_ai_explainer_structured_from_stats(
            customer=customer,
            segment=3,
            stats = stats,
            metrics=metrics,
        )
        # CC.add_email_digest(customer.id, metrics)
    except Exception:
        ai = None

    verdicts = {
        "sold_price": verdict_sentence("sold_price", ai['conclusions']['sold_price']),
        "speed":       verdict_sentence("speed",       ai['conclusions']['speed']),
        "inventory": verdict_sentence("competition", ai['conclusions']['inventory']),
   }
    labels = derive_header_fields(stats, ai)
    html_content = render_template(
        'EmailCampaignTemplate/email_sellercustomer.html',  # Your template in app/templates
        customer=customer,
        weekly_summary=weekly_summary,
        ai_history=ai_history,
        ai=ai,
        stats=stats,
        verdicts=verdicts,
        soldhomes=soldhomes,
        showScheduleButton=True,
        website='https://www.wayber.net/',
        labels=labels
    )

    try:
        if forreal:
            send_email(subject=f'{ai["title"]}- copy sent to Customer',
                       html_content=html_content,
                       recipient=defaultrecipient)

            recipient = customer.email
        else:
            recipient = defaultrecipient
        return send_email(subject=f'{ai["title"]}',
                          html_content=html_content,
                          recipient=recipient)

        # flash("The email was sent successfully!", "success")
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





