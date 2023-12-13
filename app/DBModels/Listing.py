
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime
# from datetime import Datetime
Base = declarative_base()
from app.extensions import db

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