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
from app.DBModels.Customer import Customer
import pytz
from datetime import datetime, timedelta
from app.MapTools.MappingTools import WA_geojson_features
from flask_mail import Mail, Message
from jinja2 import Environment, FileSystemLoader

# from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForForSaleHomes,
defaultrecipient = 'waichak.luk@gmail.com'
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

def sendCustomerEmail(customer:Customer,locations,
                      plot_url, soldhomes):

    # Fetch customer’s neighborhood interests
    # interests = customer.interests  # Assuming a relationship is defined
    # output_dir = Path("app/static/maps")
    # output_dir.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists
    # map_html_path = output_dir / f"map_{customer.name}.html"
    # map_image_path = output_dir / f"map_{customer.name}_screenshot.png"
    url_image_path= f"https://www.drillbreaker29.com/static/maps/map_{customer.name}_screenshot.png"
    # Create the email body
    email_subject = "Your Neighborhood Interests"
    email_html_content = render_template(
        'InterestReport/NeighbourhoodInterest.html',
        customer=customer,
        locations=locations,
        geojson_features=WA_geojson_features,
        Webpage=False,
        # homes_with_comments=homes_with_comments,
        url_image_path=url_image_path,
        plot_url=f"https://www.drillbreaker29.com/static/maps/015402.png",
        soldhouses=soldhomes
    )

    try:
        send_email(
            subject=email_subject,
            recipient='waichak.luk@gmail.com',#customer.email,  # Email address of the customer
            html_content=email_html_content
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

# def sendEmailofOpenHomes():
#     # subject, body, recipient = defaultrecipient, html_content = None
#     map_html, filtered_houses = SearchForOpenHouses()
#     send_emailforOpenHouse(filtered_houses)
#     return map_html

