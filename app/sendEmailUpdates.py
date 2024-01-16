from SMTP_email import send_email
from flask import session
import json

def sendEmailUpdatesProcess(recipient):
    # Use a subset of your listings or dummy data for testing

    # infodump = session['infodump']

    email_content = "New Listings:\n"

    # email_content += json.dumps(infodump)
    # main.logger.error('wtf')
    # raise('problem')
    send_email('New Listing', email_content,recipient)
    # main.logger.error('got to here')

