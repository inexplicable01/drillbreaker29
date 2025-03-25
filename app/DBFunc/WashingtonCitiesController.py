# from app.DBModels.WashingtonCities import WashingtonCities
from app.DBFunc.CustomerController import Customer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Double,Float, String, Text, BigInteger, DateTime, Numeric

# Base = declarative_base()
from app.extensions import db

class WashingtonCities(db.Model):
    __tablename__ = 'WashingtonCities'

    City = Column(Text)
    city_id= Column(Integer, primary_key=True)
    county = Column(Text)

    # interests = db.relationship('CustomerZone', back_populates='WashingtonCities')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return (f"<WashingtonCities(city={self.City}, city_id={self.city_id}, county={self.county}")


class WashingtonCitiesController():

    def __init__(self):
        self.db = db
        self.WashingtonCities = WashingtonCities

    def getallcities(self):
        return [c.City for c in WashingtonCities.query.all()]

    def getCity(self, City):
        return self.WashingtonCities.query.filter_by(City=City).first()

    def get_cities_by_county(self, counties):
        return [c.City for c in self.WashingtonCities.query.filter(self.WashingtonCities.county.in_(counties)).all()]

    def get_city_names_for_level1_customers(self):

        result = (
            db.session.query(self.WashingtonCities.City)
            .join(self.WashingtonCities.customers)
            .filter(Customer.customer_type_id == 1)
            .distinct()
            .all()
        )
        return [city[0] for city in result]


washingtoncitiescontroller = WashingtonCitiesController()