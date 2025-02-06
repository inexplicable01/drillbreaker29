from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from app.extensions import db
from datetime import datetime


class AIListingComments(db.Model):
    __tablename__ = 'AI_Listing_Comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id', ondelete="CASCADE"), nullable=False)
    listing_id = db.Column(db.BigInteger, db.ForeignKey('BriefListing.zpid', ondelete="CASCADE"), nullable=False)
    ai_comment = db.Column(db.Text, nullable=False)
    likelihood_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Fix: Ensure these relationships point to mapped classes
    customer = db.relationship('Customer', backref='ai_comments', lazy=True)
    listing = db.relationship('BriefListing', backref='ai_comments', lazy=True)

    # def __str__(self):
    #     return (
    #         f"Customer(ID: {self.id}, Name: {self.name}, Email: {self.email}, "
    #         f"Phone: {self.phone}, Price Range: {self.minprice}-{self.maxprice} (Ideal: {self.idealprice}), "
    #         f"Square Footage: {self.minsqft}-{self.maxsqft} (Ideal: {self.idealsqft}))"
    #     )