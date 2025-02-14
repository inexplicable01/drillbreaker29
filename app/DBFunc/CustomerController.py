from app.DBModels.Customer import Customer
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief


class CustomerController():

    def __init__(self):
        self.db = db
        self.Customer = Customer

    def getAllCustomer(self):
        return Customer.query.all()

    def getCustomerByID(self, id):
        return Customer.query.get(id)

    def getCustomerZpidInterests(self):
        customers = Customer.query.options(db.joinedload(Customer.customerzpid_array)).all()
        return customers


customercontroller = CustomerController()