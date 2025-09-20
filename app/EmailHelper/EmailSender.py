import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
# from run import app
import os
# from app.NewListing import NewListing,NewListingForEmail
FROMEMAIL = os.getenv('FROMEMAIL')
defaultrecipient='waichak.luk@gmail.com'
def send_email(subject, recipient, html_content=None) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = FROMEMAIL
        msg["To"] = recipient
        msg["Subject"] = str(Header(subject, "utf-8"))  # handle non-ASCII

        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP("smtppro.zoho.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(FROMEMAIL, os.getenv("EMAILCODE") or "")
            # send bytes, not str
            server.sendmail(FROMEMAIL, [recipient], msg.as_bytes())
        return True
    except Exception as e:
        print(f"email send failed: {e}")
        return False


def send_emailforOpenHouse( houses, app=None):
    if app:
        with app.app_context():
            send_emailofopenhomes(houses)
    else:
        send_emailofopenhomes(houses)



def send_emailofopenhomes(houses):
    msg = MIMEMultipart()
    msg['From'] = FROMEMAIL
    msg['To'] = defaultrecipient
    msg['Subject'] = 'Static Daily'

    msg.attach(MIMEText('bod', 'plain', 'utf-8'))

    # html_content = NewListingForEmail('Seattle', 1)
    sorted_houses = sorted(houses, key=lambda x: x['daysOnZillow'])


    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(FROMEMAIL, os.getenv('EMAILCODE'))
        text = msg.as_string().encode('utf-8')
        server.sendmail(FROMEMAIL, defaultrecipient, text)

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