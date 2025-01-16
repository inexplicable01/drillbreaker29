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

def sendEmailpending():
    # subject, body, recipient = defaultrecipient, html_content = None
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(seattle_tz)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    citiesdata = citystatscachecontroller.get_all_city_stats()
    # Prepare the email content
    table_rows = ""
    for citydata in citiesdata:
        table_rows += f"""
        <tr>
            <td>{citydata.city_name}</td>
            <td>{citydata.sold}</td>
            <td>{citydata.pending}</td>
            <td>{citydata.forsale}</td>
            <td>{citydata.updated_time.astimezone(seattle_tz).strftime(
                '%m/%d/%Y %I:%M %p %A') if citydata.updated_time else "N/A"}</td>
        </tr>
        """
        # Prepare the email content
    html_content = f"""
     <html>
         <body>
             <p>The email was sent on {formatted_time} (Seattle Time).</p>
             <p>Here is the latest data:</p>
             <table border="1">
                 <thead>
                 <tr>
                     <th>City</th>
                     <th>Sold</th>
                     <th>Pending</th>
                     <th>For Sale</th>
                     <th>Latest Brief Listing</th>
                 </tr>
                 </thead>
                 <tbody>
                     {table_rows}
                 </tbody>
             </table>
         </body>
     </html>
     """

    # html_content=''
    send_email(subject='NewListing',
               html_content=html_content,
               recipient =defaultrecipient)


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

