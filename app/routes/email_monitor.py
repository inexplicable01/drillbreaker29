import imaplib
import email
from email.header import decode_header
import time
import os
from dotenv import load_dotenv
# email_bp.py
from flask import Blueprint, redirect, url_for,request, jsonify
from datetime import datetime, timedelta
from app.DBFunc.EmailController import emailcontroller
# platformSMSBP = Blueprint('platformSMS', __name__, url_prefix='/platformSMS')

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SERVER = os.getenv("SERVER")
PORT = os.getenv("PORT")

emailmonitorbp = Blueprint('emailmonitor', __name__, url_prefix='/emailmonitor')


@emailmonitorbp.route('/messageupload', methods=['POST'])
def check_inbox():
    emailcontroller.check_inbox()


def handle_email(sender, subject, body):
    # Define actions based on sender and content
    if "specific_sender@example.com" in sender:
        print(f"Handling email from {sender}")
        if "specific keyword" in body:
            print("Taking action based on email content")
