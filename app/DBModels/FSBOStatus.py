from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db
from datetime import datetime, timedelta
from app.useful_func import safe_float_conversion,safe_int_conversion
import decimal

class FSBOStatus(db.Model):
    __tablename__ = 'FSBOStatus'

    zpid = db.Column(db.BigInteger, db.ForeignKey('BriefListing.zpid'), primary_key=True)
    hasContactedOnline = db.Column(db.Boolean, default=False)
    hasPostCarded = db.Column(db.Boolean, default=False)
    contactedOnlineTimestamp = db.Column(db.DateTime, nullable=True)
    postcardedTimestamp = db.Column(db.DateTime, nullable=True)
    # No backref here, just a regular relationship
    # brief_listing_reference = db.relationship('BriefListing', lazy=True)

    def __str__(self):
        return f"FSBO Status for {self.zpid}: Contacted Online - {self.hasContactedOnline}, Postcarded - {self.hasPostCarded}"

    def to_dict(self):
        return {
            'hasContactedOnline': self.hasContactedOnline,
            'hasPostCarded': self.hasPostCarded,
        }