from app.DBModels.WACities import WashingtonCities
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief


class WashingtonCitiesController():

    def __init__(self):
        self.db = db
        self.WashingtonCities = WashingtonCities

    def getallcities(self):
        return [c.city for c in WashingtonCities.query.all()]



washingtoncitiescontroller = WashingtonCitiesController()