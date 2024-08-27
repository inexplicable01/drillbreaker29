from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db

class SMS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<SMS {self.sender}>'
