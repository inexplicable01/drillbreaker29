
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime
# from datetime import Datetime
Base = declarative_base()
from app.extensions import db
from datetime import datetime
def safe_float_conversion(value, default=0.0):
    try:
        return float(value)
    except ValueError:
        return default


def safe_int_conversion(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default

class Listing(db.Model):
    __tablename__ = 'Listing'  # specify your table name here

    id = db.Column(db.Integer, primary_key=True)
    zpid = db.Column(db.Integer, unique=True, nullable=False)
    price = db.Column(db.Float, nullable=True, default=0.0)
    unit = db.Column(db.String(255), nullable=True)  # Specify length here
    streetAddress = db.Column(db.String(255), nullable=True)  # And here
    city = db.Column(db.String(100), nullable=True)  # And so on...
    state = db.Column(db.String(50), nullable=True)
    zipcode = db.Column(db.String(20), nullable=True)
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Float, nullable=True, default=0.0)
    zestimate = db.Column(db.Float, nullable=True, default=0.0)
    daysOnZillow = db.Column(db.Integer, nullable=True, default=0)
    dateSold = db.Column(db.DateTime, nullable=True)
    homeType = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True, default=0.0)
    longitude = db.Column(db.Float, nullable=True, default=0.0)
    list2pend = db.Column(db.Integer, nullable=True, default=0)
    list2pendCheck = db.Column(db.Integer, nullable=True, default=0)
    status = db.Column(db.String(50), nullable=True, default='sold')

    @classmethod
    def CreateListing(cls, house, status):
        if 'datesold' not in house.keys():
            house['dateSold'] = 0
        try:
            new_address = cls()
            new_address.zpid = house['zpid']
            new_address.price = house.get('price', 0)
            new_address.unit =  house.get('unit', 'Null') # Specify length here
            new_address.streetAddress = house.get('streetAddress', 'Missing') # And here
            new_address.city = house.get('city', 'Missing')   # And so on...
            new_address.state = house.get('state', 'Missing')
            new_address.zipcode = safe_int_conversion(house.get('zipcode', 90000) )
            new_address.bedrooms = safe_int_conversion(house.get('bedrooms', 0) )
            new_address.bathrooms = safe_float_conversion(house.get('bathrooms', 0) )
            new_address.zestimate = safe_float_conversion(house.get('zestimate', 0)),
            new_address.daysOnZillow = safe_int_conversion(house.get('daysOnZillow', 999)),
            new_address.dateSold = datetime.utcfromtimestamp(int(house.get('dateSold',datetime.now())) / 1000)
            new_address.homeType = house.get('homeType', 'Single_Family')
            new_address.latitude = safe_float_conversion(house.get('latitude',0))
            new_address.longitude = safe_float_conversion(house.get('longitude',0))
            new_address.list2pend = 0
            new_address.list2pendCheck = 0
            new_address.status = status
            return new_address
        except Exception as e:
            print(e)
            return cls()