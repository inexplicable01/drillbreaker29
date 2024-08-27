# email_bp.py
from flask import Blueprint, redirect, url_for,request, jsonify
from datetime import datetime, timedelta
from app.DBFunc.SMSDBController import smscontroller

platformSMSBP = Blueprint('platformSMS', __name__, url_prefix='/platformSMS')


@platformSMSBP.route('/messageupload', methods=['POST'])
def messageupload():
    sender = request.form.get('sender')
    message = request.form.get('message')
    smscontroller.addnewmessage(sender,message)
    return "Message received and stored", 200