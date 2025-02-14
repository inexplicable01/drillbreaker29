from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
Base = declarative_base()
from app.extensions import db
from datetime import datetime, timedelta
from app.useful_func import safe_float_conversion,safe_int_conversion
import decimal
# from app.DBModels.CustomerZpid import CustomerZpid
# from app.models.brief_listing import BriefListing


class BriefListing(db.Model):
    __tablename__= 'BriefListing'

    zpid = db.Column(db.BigInteger, primary_key=True, nullable=True)
    NWMLS_id = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Float, nullable=True, default=1.0)
    bedrooms = db.Column(db.Float, nullable=True, default=1.0)
    city = db.Column(db.String(255), nullable=True)  # Specify length here
    country = db.Column(db.String(255), nullable=True)
    # currency = db.Column(db.String(10), nullable=True)
    dateSold = db.Column(BigInteger, nullable=True)
    daysOnZillow = db.Column(db.Integer, nullable=True)
    homeStatus = db.Column(db.String(100), nullable=True)
    homeStatusForHDP = db.Column(db.String(100), nullable=True)
    homeType = db.Column(db.String(100), nullable=True)
    imgSrc = db.Column(db.String(255), nullable=True)
    isFeatured = db.Column(db.Boolean, nullable=True)
    isNonOwnerOccupied = db.Column(db.Boolean, nullable=True)
    isPreforeclosureAuction = db.Column(db.Boolean, nullable=True)
    isPremierBuilder = db.Column(db.Boolean, nullable=True)
    isShowcaseListing = db.Column(db.Boolean, nullable=True)
    isUnmappable = db.Column(db.Boolean, nullable=True)
    isZillowOwned = db.Column(db.Boolean, nullable=True)
    latitude = db.Column(Numeric(precision=10,scale=7), nullable=True)
    livingArea = db.Column(db.Float, nullable=True)
    longitude = db.Column(Numeric(precision=10,scale=7), nullable=True)
    price = db.Column(db.BigInteger, nullable=True)
    priceForHDP = db.Column(db.Float, nullable=True)
    shouldHighlight = db.Column(db.Boolean, nullable=True)
    state = db.Column(db.String(100), nullable=True)
    streetAddress = db.Column(db.String(255), nullable=True)
    zipcode = db.Column(db.String(20), nullable=True)
    # zpid = db.Column(db.BigInteger, unique=True, nullable=True)
    list2penddays = db.Column(db.Integer, nullable=True)
    list2solddays = db.Column(db.Integer, nullable=True)
    listprice = db.Column(db.BigInteger, nullable=True)
    zestimate = db.Column(db.BigInteger, nullable=True)
    taxAssessedValue = db.Column(db.Float, nullable=True)
    lotAreaUnit = db.Column(db.String(50), nullable=True)
    lotAreaValue = db.Column(db.Float, nullable=True)
    # listing_sub_type = db.Column(JSON, default={})
    rentZestimate = db.Column(db.BigInteger, nullable=True)
    # unit = db.Column(db.String(50), nullable=True)
    # videoCount = db.Column(db.String(50), nullable=True)
    # isRentalWithBasePrice = db.Column(db.Boolean, nullable=True)
    newConstructionType = db.Column(db.String(100), nullable=True)
    hdpUrl = db.Column(db.String(255), nullable=True)
    pricedelta = db.Column(db.BigInteger, nullable=True)
    neighbourhood = db.Column(db.String(50), nullable=True)
    neighbourhood_sub = db.Column(db.String(100), nullable=True)
    gapis_neighbourhood=db.Column(db.String(50), nullable=True)
    zillowapi_neighbourhood = db.Column(db.String(50), nullable=True)
    search_neigh = db.Column(db.String(50), nullable=True)
    listday = db.Column(BigInteger, nullable=True)
    pendday = db.Column(BigInteger, nullable=True)
    listtime = db.Column(BigInteger, nullable=True)
    soldBy = db.Column(db.String(100), nullable=True)
    waybercomments = db.Column(db.String(255), nullable=True)
    openhouseneed = db.Column(db.Boolean,nullable=True)

    # Define the one-to-one relationship to FSBOStatus
    fsbo_status = db.relationship('FSBOStatus', backref='brief_listing', uselist=False, lazy=True)
    # customers = db.relationship(
    #     'CustomerZpid',
    #     back_populates="brief_listing",  # Bidirectional relationship
    #     cascade="all, delete-orphan"
    # )

    def __post_init__(self, extras):
        # This method now accepts `extras` but does nothing with it,
        # effectively ignoring any unexpected keys.
        pass

    def ref_address(self):
        return f"{self.streetAddress}_{self.city}_{self.zipcode}".replace(' ', '_')

    def updateListingLength(self,listinglength):
        self.list2penddays=listinglength['list2penddays']
        self.list2solddays = listinglength['list2solddays']
        self.listprice = listinglength['listprice']
        if self.listprice is not None:
            self.pricedelta=self.price-self.listprice

    def __str__(self):
        return str(self.zpid) + ' ' + self.streetAddress + ' ' + self.city

    def to_dict(self):
        return {
            'zpid': self.zpid,
            'streetAddress': self.streetAddress,
            'city': self.city,
            'state': self.state,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'price': self.price,
            'soldBy': self.soldBy,
            'homeStatus': self.homeStatus,
            'neighbourhood': self.neighbourhood,
            'dateSold': self.dateSold,
            'waybercomments':self.waybercomments,
            'fsbostatus': self.fsbo_status,
            'bathrooms': self.bathrooms,
            'bedrooms': self.bedrooms,
            'hdpUrl': self.hdpUrl,
            'imgSrc': self.imgSrc,
        }

    def getPropertyData(self):
        propertydata = loadPropertyDataFromBrief(self)
        listresults = ListingLengthbyBriefListing(propertydata)
        self.updateListingLength(listresults)
        self.hdpUrl = propertydata['hdpUrl']
        try:
            self.NWMLS_id = propertydata['attributionInfo']['mlsId']
        except Exception as e:
            print(e, self)


    @classmethod
    def CreateBriefListing(cls, briefhomedata, neighbourhood, zillowapi_neighbourhood, search_neigh):
        try:
            new_listing = cls()
            new_listing.zpid = briefhomedata.get('zpid')
            new_listing.neighbourhood = neighbourhood
            new_listing.zillowapi_neighbourhood = zillowapi_neighbourhood
            new_listing.search_neigh = search_neigh
            new_listing.bathrooms = safe_float_conversion(briefhomedata.get('bathrooms', 1.0))
            new_listing.bedrooms = safe_float_conversion(briefhomedata.get('bedrooms', 1.0))
            new_listing.city = briefhomedata.get('city', 'Missing')
            new_listing.country = briefhomedata.get('country', 'Missing')
            # new_listing.currency = briefhomedata.get('currency', 'Missing')
            new_listing.livingArea=safe_float_conversion(briefhomedata.get('livingArea', 1.0))
            new_listing.dateSold = safe_int_conversion(
                briefhomedata.get('dateSold', 0))  # Consider datetime conversion if necessary
            new_listing.daysOnZillow = safe_int_conversion(briefhomedata.get('daysOnZillow', 0))
            new_listing.homeStatus = briefhomedata.get('homeStatus', 'Missing')
            new_listing.homeStatusForHDP = briefhomedata.get('homeStatusForHDP', 'Missing')
            new_listing.homeType = briefhomedata.get('homeType', 'Missing')
            new_listing.imgSrc = briefhomedata.get('imgSrc', 'Missing')
            new_listing.isFeatured = briefhomedata.get('isFeatured', False)
            new_listing.isNonOwnerOccupied = briefhomedata.get('isNonOwnerOccupied', False)
            new_listing.isPreforeclosureAuction = briefhomedata.get('isPreforeclosureAuction', False)
            new_listing.isPremierBuilder = briefhomedata.get('isPremierBuilder', False)
            new_listing.isShowcaseListing = briefhomedata.get('isShowcaseListing', False)
            new_listing.isUnmappable = briefhomedata.get('isUnmappable', False)
            new_listing.isZillowOwned = briefhomedata.get('isZillowOwned', False)
            new_listing.latitude = decimal.Decimal(briefhomedata.get('latitude', '0.0000000'))
            new_listing.longitude = decimal.Decimal(briefhomedata.get('longitude', '0.0000000'))
            new_listing.price = safe_int_conversion(briefhomedata.get('price', 0))
            new_listing.state = briefhomedata.get('state', 'Missing')
            new_listing.streetAddress = briefhomedata.get('streetAddress', 'Missing')
            new_listing.zipcode = briefhomedata.get('zipcode', 'Missing')
            new_listing.list2penddays = safe_int_conversion(briefhomedata.get('list2penddays', 0))
            new_listing.list2solddays = safe_int_conversion(briefhomedata.get('list2solddays', 0))
            new_listing.listprice = safe_int_conversion(briefhomedata.get('listprice', 0))
            new_listing.zestimate = safe_int_conversion(briefhomedata.get('zestimate', 0))
            new_listing.taxAssessedValue = safe_float_conversion(briefhomedata.get('taxAssessedValue', 0.0))
            new_listing.lotAreaUnit = briefhomedata.get('lotAreaUnit', 'Missing')
            new_listing.lotAreaValue = safe_float_conversion(briefhomedata.get('lotAreaValue', 0.0))
            # Assuming `listing_sub_type` is passed as a dictionary and directly assignable
            new_listing.listing_sub_type = briefhomedata.get('listing_sub_type', {})
            new_listing.rentZestimate = safe_int_conversion(briefhomedata.get('rentZestimate', 0))
            # Assuming that for optional fields without defaults you want to use None or a sentinel value
            new_listing.unit = briefhomedata.get('unit', None)  # Handling for 'unit' as optional
            new_listing.videoCount = briefhomedata.get('videoCount', '0')  # Assuming '0' as default for missing
            # new_listing.isRentalWithBasePrice = briefhomedata.get('isRentalWithBasePrice', False)
            new_listing.newConstructionType = briefhomedata.get('newConstructionType', 'Missing')
            new_listing.hdpUrl = briefhomedata.get('hdpUrl', 'Missing')
            new_listing.pricedelta = safe_int_conversion(briefhomedata.get('pricedelta', 0))

            listing_time = datetime.utcnow() - timedelta(seconds=safe_int_conversion(briefhomedata.get('timeOnZillow', 0))/1000)
            new_listing.listtime = int(listing_time.timestamp())
            new_listing.soldBy = "AGENT"

            return new_listing

        except Exception as e:
            print('Create Listing Error', e)
            return None

# Example usage:
response = {
    'bathrooms': 3.0,
    'bedrooms': 5.0,
    'city': 'Seattle',
    'country': 'USA',
    'currency': 'USD',
    'dateSold': 1708934400000,
    'daysOnZillow': 1,
    'homeStatus': 'RECENTLY_SOLD',
    'homeStatusForHDP': 'RECENTLY_SOLD',
    'homeType': 'SINGLE_FAMILY',
    'imgSrc': 'https://photos.zillowstatic.com/fp/a6ad1b1713ff7fb31f4bdf9b9a96d879-p_e.jpg',
    'isFeatured': False,
    'isNonOwnerOccupied': True,
    'isPreforeclosureAuction': False,
    'isPremierBuilder': False,
    'isShowcaseListing': False,
    'isUnmappable': False,
    'isZillowOwned': False,
    'latitude': 47.68349,
    'listing_sub_type': {},
    'livingArea': 3017.0,
    'longitude': -122.37754,
    'lotAreaUnit': 'sqft',
    'lotAreaValue': 3706.956,
    'price': 1502000.0,
    'priceForHDP': 1502000.0,
    'rentZestimate': 4920,
    'shouldHighlight': False,
    'state': 'WA',
    'streetAddress': '7506 16th Avenue NW',
    'taxAssessedValue': 1093000.0,
    'timeOnZillow': 117845000,
    'zestimate': 1445600,
    'zipcode': '98117',
    'zpid': 48714500
}

# property_details = BriefListing(**response)
# print(property_details)
def filter_dataclass_fields(data, dataclass_type):
    """
    Filter a dictionary to contain only keys that are valid fields of the specified dataclass.

    :param data: Dictionary containing data to be filtered.
    :param dataclass_type: The dataclass type to filter the data against.
    :return: A new dictionary with only the keys that are valid fields of the dataclass.
    """
    valid_keys = {field.name for field in fields(dataclass_type)}
    return {key: value for key, value in data.items() if key in valid_keys}