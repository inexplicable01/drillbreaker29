from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Double,Float, String, Text, BigInteger, DateTime, Numeric

# Base = declarative_base()
from app.extensions import db

class WashingtonCities(db.Model):
    __tablename__ = 'WashingtonCities'

    city = Column(Text)
    city_id= Column(Integer, primary_key=True)
    county = Column(Text)

    interests = db.relationship('CustomerNeighbourhoodInterest', back_populates='WashingtonCities')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return (f"<WashingtonCities(city={self.city}, city_id={self.city_id}, county={self.county}")

