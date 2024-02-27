import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from run import app
import os
from app.NewListing import NewListing,NewListingForEmail
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

def send_emailforOpenHouse( houses, app=None):
    if app:
        with app.app_context():
            send_emailofopenhomes(houses)
    else:
        send_emailofopenhomes(houses)

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


def send_emailofopenhomes(houses):
    msg = MIMEMultipart()
    msg['From'] = fromemail
    msg['To'] = defaultrecipient
    msg['Subject'] = 'Static Daily'

    msg.attach(MIMEText('bod', 'plain', 'utf-8'))

    # html_content = NewListingForEmail('Seattle', 1)
    sorted_houses = sorted(houses, key=lambda x: x['daysOnZillow'])
    html_content = '''
    <table border="1">
        <tr>
            <th>Link</th>
            <th>Price</th>
            <th>Beds</th>
            <th>Bath</th>
            <th>Square ft</th>
            <th>Days on Market</th>
            <th>Agent Name</th>
            <th>Agent Number</th>
            <th>Neighbourhood</th>
        </tr>'''

    for house in sorted_houses:
        row = f'''
        <tr>
            <td><a href='https://www.zillow.com{house['hdpUrl']}' target='_blank'>House Link</a></td>
            <td>{house['price']}</td>
            <td>{house['bedrooms']}</td>
            <td>{house['bathrooms']}</td>
            <td>{house['livingArea']}</td>
            <td>{house['daysOnZillow']}</td>
            <td>{house['attributionInfo']['agentName']}</td>
            <td>{house['attributionInfo']['agentPhoneNumber']}</td>
            <td>{house.get('neighborhoodRegion', {}).get('name', 'N/A')}</td>
        </tr>
        '''
        html_content += row
    html_content += '</table>'
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