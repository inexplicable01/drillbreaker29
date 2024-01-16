from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger
from datetime import datetime
from app.extensions import db
Base = declarative_base()

def safe_float_conversion(value, default=0.0):
    try:
        return float(value)
    except ValueError:
        return default


def safe_int_conversion(value, default=0):
    try:
        if value is None:
            return 0
        return int(value)
    except ValueError:
        return default
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
    haswaterfrontview = db.Column(db.Integer, default=False)

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

    @classmethod
    def create_from_dict(cls, propertydata):
        # Create an instance of BellevueTaxAddress
        new_address = cls()
        new_address.addr_full = propertydata['address']['streetAddress']
        new_address.sitetype = propertydata['resoFacts']['zoningDescription']
        new_address.zip5 = propertydata['zipcode']
        new_address.postalcityname = propertydata['address']['city']
        new_address.latitude = float(propertydata['latitude'])
        new_address.longitude = float(propertydata['longitude'])
        try:
            new_address.shape_area = float(propertydata['lotSize'])
        except:
            print("No Lot Size")
        new_address.zestimate_value = safe_int_conversion(propertydata.get('zestimate',0))# Allows NULL values
        new_address.year_built = int(propertydata['yearBuilt'])  # Allows NULL values
        new_address.living_area = int(propertydata['livingArea'])   # Allows NULL values
        new_address.bathrooms = float(propertydata['bathrooms'])  # Allows NULL values
        new_address.bedrooms = float(propertydata['bedrooms'])  # Allows NULL values
        new_address.home_type = propertydata['homeType'] # Allows NULL values
        new_address.haswaterfrontview = propertydata['resoFacts']['hasWaterfrontView']
        # Iterate over the dictionary, assigning values to the new instance

        # Add the new instance to the session and commit
        db.session.add(new_address)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        return new_address

    def dictify(self):

        return
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