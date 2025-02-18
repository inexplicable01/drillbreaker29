from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db


class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    minprice = db.Column(db.Integer, nullable=True)
    idealprice = db.Column(db.Integer, nullable=True)
    maxprice = db.Column(db.Integer, nullable=True)
    idealsqft = db.Column(db.Integer, nullable=True)
    minsqft = db.Column(db.Integer, nullable=True)
    maxsqft = db.Column(db.Integer, nullable=True)


    interests = db.relationship('CustomerZone', back_populates='customer')


    def __str__(self):
        return (
            f"Customer(ID: {self.id}, Name: {self.name}, Email: {self.email}, "
            f"Phone: {self.phone}, Price Range: {self.minprice}-{self.maxprice} (Ideal: {self.idealprice}), "
            f"Square Footage: {self.minsqft}-{self.maxsqft} (Ideal: {self.idealsqft}))"
        )