from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db
from datetime import datetime

class CustomerZpid(db.Model):
    __tablename__ = 'CustomerZpid'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id', ondelete="CASCADE"))
    zpid = db.Column(db.BigInteger, db.ForeignKey('BriefListing.zpid', ondelete="CASCADE"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())


    def __init__(self, customer_id, zpid,created_at):
        self.customer_id = customer_id
        self.zpid = zpid
        self.created_at=created_at

    def __repr__(self):
        return f"<CustomerZpids id={self.id} customer_id={self.customer_id} zpid={self.zpid}>"
