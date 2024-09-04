from app.DBModels.TaxRateModel import RealEstateExciseTaxRates
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief


class TaxRatesController():

    def __init__(self):
        self.db = db
        self.RealEstateExciseTaxRates = RealEstateExciseTaxRates

    def getAllCleaners(self):
        return RealEstateExciseTaxRates.query.all()

    def getTaxRateByCity(self,city):
        return self.RealEstateExciseTaxRates.query.filter(
            self.RealEstateExciseTaxRates.location.ilike(f"%{city}%")
        ).first()


taxratescontroller = TaxRatesController()