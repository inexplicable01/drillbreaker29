import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from run import app
import os
from flask import render_template
from app.config import Config
from app.NewListing import NewListing,NewListingForEmail
from app.EmailHelper.EmailSender import send_email , send_emailforOpenHouse
from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForForSaleHomes,loadPropertyDataFromBrief
from app.DBFunc.CityStatsCacheController import citystatscachecontroller
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBModels.BriefListing import BriefListing
from datetime import datetime
import pytz
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


from datetime import datetime, timedelta
import pytz
from jinja2 import Environment, FileSystemLoader


def sendEmailpending():
    # Define Seattle timezone
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')

    # Fetch all city statistics
    citiesdata = citystatscachecontroller.get_all_city_stats()

    # Prepare city statistics for the template
    city_stats = [
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
        city_stats=city_stats,
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

