# from app.DBModels.WashingtonCities import WashingtonCities
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Double,Float, String, Text, BigInteger, DateTime, Numeric

# Base = declarative_base()
from app.extensions import db

class WashingtonCities(db.Model):
    __tablename__ = 'WashingtonCities'

    City = Column(Text)
    city_id= Column(Integer, primary_key=True)
    county = Column(Text)

    # interests = db.relationship('CustomerZone', back_populates='WashingtonCities')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return (f"<WashingtonCities(city={self.City}, city_id={self.city_id}, county={self.county}")


class WashingtonCitiesController():

    def __init__(self):
        self.db = db
        self.WashingtonCities = WashingtonCities

    def getallcities(self):
        return [c.City for c in WashingtonCities.query.all()]

    def getCity(self, City):
        return self.WashingtonCities.query.filter_by(City=City).first()

    def get_cities_by_county(self, counties):
        return [c.City for c in self.WashingtonCities.query.filter(self.WashingtonCities.county.in_(counties)).all()]


washingtoncitiescontroller = WashingtonCitiesController()