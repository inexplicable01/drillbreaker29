from app.DBFunc.WashingtonZonesController import WashingtonZones
from app.extensions import db
from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from sqlalchemy.orm import relationship
from app.DBFunc.WashingtonCitiesController import WashingtonCities
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric , ForeignKey

from app.DBFunc.CustomerController import Customer
# from app.DBModels.CustomerZone import CustomerZone
from typing import Optional

Base = declarative_base()
from app.extensions import db

class CustomerZone(db.Model):
    __tablename__ = 'CustomerZone'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('WashingtonZones.id'), nullable=False)
    # city_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id'), nullable=False)
    #zone = db.relationship("WashingtonZones", back_populates="interests")
    #customer = db.relationship('Customer', back_populates='interests')
    #zone = db.relationship('WashingtonZones', back_populates='interests')
    # WashingtonCities = db.relationship('WashingtonCities', back_populates='interests')

class CustomerZoneController:
    def __init__(self):
        self.db = db
        self.WashingtonZones = WashingtonZones
        self.Customer = Customer
        self.CustomerZone = CustomerZone

    def get_customer_zone(self, customer_id):
        # Fetch customer details
        customer = self.Customer.query.filter_by(id=customer_id).first()
        if not customer:
            return None, []  # Return None if the customer is not found

        return customer

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """
        Fetch customer details and ensure it returns an instance of Customer or None.
        """
        customer: Optional[Customer] = Customer.query.filter_by(id=customer_id).first()
        return customer

customerzonecontroller = CustomerZoneController()
