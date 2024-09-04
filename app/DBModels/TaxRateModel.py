from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Double,Float, String, Text, BigInteger, DateTime, Numeric

Base = declarative_base()
from app.extensions import db

class RealEstateExciseTaxRates(db.Model):
    __tablename__ = 'Real_Estate_Excise_Tax_Rates'

    code = Column(Double, primary_key=True)
    county = Column(Text)
    location = Column(Text)
    local_rate = Column(Double)
    combined_rate = Column(Double)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
