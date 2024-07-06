from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db

class Cleaners(db.Model):
    __tablename__ = 'Cleaners'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    created_date = db.Column(db.String)
    updated_date = db.Column(db.String)
    owner = db.Column(db.String)
    review_ratings = db.Column(db.Float)
    price = db.Column(db.Float)
    company_website = db.Column(db.String)
    picture_link = db.Column(db.String)
    company_description = db.Column(db.String)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}