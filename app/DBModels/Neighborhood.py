from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db
from sqlalchemy.orm import relationship

class Neighborhood(Base):
    __tablename__ = 'Neighborhoods'
    id = Column(Integer, primary_key=True)
    neighborhood = Column(String(50), nullable=False)
    neighborhood_sub = Column(String(50))

    interests = relationship('CustomerNeighborhoodInterest', back_populates='neighborhood')
