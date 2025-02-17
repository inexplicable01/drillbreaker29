from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from sqlalchemy.orm import relationship
from app.DBModels.WashingtonCities import WashingtonCities
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric , ForeignKey
Base = declarative_base()
from app.extensions import db

class CustomerNeighbourhoodInterest(db.Model):
    __tablename__ = 'CustomerNeighbourhoodInterest'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    neighbourhood_id = db.Column(db.Integer, db.ForeignKey('WashingtonZones.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id'), nullable=False)

    customer = db.relationship('Customer', back_populates='interests')
    neighbourhood = db.relationship('WashingtonZones', back_populates='interests')
    WashingtonCities = db.relationship('WashingtonCities', back_populates='interests')