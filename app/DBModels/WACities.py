from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Double,Float, String, Text, BigInteger, DateTime, Numeric

Base = declarative_base()
from app.extensions import db

class WashingtonCities(db.Model):
    __tablename__ = 'WashingtonCities'

    city = Column(Text, primary_key=True)


    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
