import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from run import app
import os
from app.NewListing import NewListing,NewListingForEmail
from app.EmailHelper.EmailSender import send_email , send_emailforOpenHouse
defaultrecipient = 'waichak.luk@gmail.com'
def sendEmailwithNewListing():
    # subject, body, recipient = defaultrecipient, html_content = None
    html_content = NewListingForEmail('Seattle', 1)
    send_email(subject='NewListing',
               html_content=html_content,
               recipient =defaultrecipient)

def sendEmailofOpenHomes():
    # subject, body, recipient = defaultrecipient, html_content = None
    map_html, filtered_houses = SearchForOpenHouses()




    send_emailforOpenHouse(filtered_houses)


    return map_html

