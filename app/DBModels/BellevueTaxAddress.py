from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger
from datetime import datetime
from app.extensions import db
Base = declarative_base()

class BellevueTaxAddress(db.Model):
    __tablename__ = 'BellevueTaxAddress'  # specify your table name here

    id = db.Column(db.Integer, primary_key=True)
    addr_full = db.Column(db.String(255))
    comments = db.Column(db.Text)
    sitetype = db.Column(db.String(5))
    zip5 = db.Column(db.Integer)
    postalcityname = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    point_x = db.Column(db.Float)
    point_y = db.Column(db.Float)
    shape_length = db.Column(db.Float)
    shape_area = db.Column(db.Float)
    zestimate_value = db.Column(db.BigInteger, nullable=True)  # Allows NULL values
    year_built = db.Column(db.Integer, nullable=True)  # Allows NULL values
    living_area = db.Column(db.Integer, nullable=True)  # Allows NULL values
    bathrooms = db.Column(db.Float, nullable=True)  # Allows NULL values
    bedrooms = db.Column(db.Float, nullable=True)  # Allows NULL values
    home_type = db.Column(db.String(20), nullable=True)  # Allows NULL values
    newbuild_prediction = db.Column(db.Float, nullable=True)  # Allows NULL values

    def __repr__(self):
        return f"<BellevueTaxAddress {self.addr_full}>"

    def detailStr(self):
        return f"{self.addr_full}, " \
               f" {self.postalcityname}," \
               f"{round(self.zestimate_value)}," \
               f" {self.sitetype}," \
               f"{self.bedrooms} beds," \
               f"{self.bathrooms} baths"
               # f"{self.longitude} + {self.latitude}\n"

    def price_vs_prediction_printout(self):
        return f"{self.addr_full}, " \
               f" {self.postalcityname}," \
               f" {self.sitetype}," \
               f"{self.bedrooms} beds," \
               f"{self.bathrooms} baths," \
               f"{self.living_area} living area\n," \
               f"est:{str(round(self.zestimate_value))}\n," \
               f"Pred:{str(round(self.newbuild_prediction))}\n,"\
               f"BuildValue:{str(round(self.newbuild_prediction-self.zestimate_value))}"

    # addr_full = parts[0]
    # postalcityname = parts[1]
    # zestimate_value = int(parts[2])
    # sitetype = parts[3]
    # bedrooms = float(parts[4].split()[0])  # Split "4.0 beds" and take the first part
    # bathrooms = float(parts[5].split()[0])  # Split "3.0 baths" and take the first part
    # living_area = int(parts[6].split()[0])  # Split "2230 baths" and take the first part
    #
    # # For 'est', 'Pred', and 'BuildValue', split by ':' and take the second part
    # est_value = int(parts[7].split(':')[1])
    # pred_value = float(parts[8].split(':')[1])
    # build_value = float(parts[9].split(':')[1])