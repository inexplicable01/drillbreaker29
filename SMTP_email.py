import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from run import app
import os
from app.NewListing import NewListing,NewListingForEmail,NewListingInNeighbourhoods
defaultrecipient = 'waichak.luk@gmail.com'
fromemail = 'wehamanagement@gmail.com'

def send_email( subject, body, recipient =defaultrecipient, html_content=None):
    msg = MIMEMultipart()
    msg['From'] = fromemail
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    if html_content:
        msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(fromemail, os.getenv('EMAILCODE'))
        text = msg.as_string()
        server.sendmail(fromemail, recipient, text)
    print('email sent')

def send_emailtest(app=None):
    if app:
        with app.app_context():
            send_emailstatic()
    else:
        send_emailstatic()

def send_emailstatic():
    msg = MIMEMultipart()
    msg['From'] = fromemail
    msg['To'] = defaultrecipient
    msg['Subject'] = 'Static Daily'

    msg.attach(MIMEText('body', 'plain', 'utf-8'))

    html_content = NewListingForEmail('Seattle', 1)

    # how to convert housedataintohtml_contnet
    if html_content:
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(fromemail, os.getenv('EMAILCODE'))
        text = msg.as_string().encode('utf-8')
        server.sendmail(fromemail, defaultrecipient, text)

# def send_email(listings):
#     # Placeholder for your email sending logic
#
#
#     try:
#         print("Attempting to send email...")
#
#         msg.attach(MIMEText(email_content, 'plain'))
#         with smtplib.SMTP('smtp.gmail.com', 587) as server:
#             server.starttls()
#             server.login("wehamanagement@gmail.com", "ennyprrdtpvpxalh")
#             text = msg.as_string()
#             print(text)
#             server.sendmail("wehamanagement@gmail.com", "waichak.luk@gmail.com", text)
#         print("Email sent!")
#     except Exception as e:
#         print(f"Error: {e}")