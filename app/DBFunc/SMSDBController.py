from app.DBModels.CleanerDBModel import Cleaners
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief
from app.DBModels.SMSDBModel import SMS

class SMSController():

    def __init__(self):
        self.db = db
        self.SMS = SMS

    def addnewmessage(self,sender,message):
        new_sms = self.SMS(sender=sender, message=message)
        self.db.session.add(new_sms)
        self.db.session.commit()
        return Cleaners.query.all()


smscontroller = SMSController()