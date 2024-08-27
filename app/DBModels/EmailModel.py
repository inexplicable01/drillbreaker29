from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Email {self.sender}>'
