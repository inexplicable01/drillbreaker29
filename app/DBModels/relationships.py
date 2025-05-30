from app.DBFunc.CustomerDescriptionController import CustomerDescription
from app.DBFunc.CustomerController import Customer
from app.DBModels.BriefListing import BriefListing
from app.DBModels.CustomerZpid import CustomerZpid
from app.DBFunc.CachedInvestmentController import CachedInvestmentData
from app.DBFunc.WashingtonZonesController import WashingtonZones
from app.DBFunc.CustomerZoneController import CustomerZone
from app.DBFunc.ZoneStatsCacheController import ZoneStatsCache
from app.DBFunc.WashingtonCitiesController import WashingtonCities
from app.DBFunc.PropertyListingController import PropertyListing
from app.DBFunc.CustomerTypeController import CustomerType
from app.DBModels.property_types import PropertyType
from app import db

# Define relationships explicitly
Customer.customerzpid_array = db.relationship(
    'CustomerZpid',  # Use the association table explicitly
    back_populates="customer",
    cascade="all, delete-orphan"
)

Customer.zones = db.relationship('CustomerZone', back_populates='customer')

BriefListing.customers = db.relationship(
    'CustomerZpid',
    back_populates="brief_listing",
    cascade="all, delete-orphan"
)

CustomerZpid.customer = db.relationship(
    "Customer",
    back_populates="customerzpid_array"
)

CustomerZpid.brief_listing = db.relationship(
    "BriefListing",
    back_populates="customers"
)

BriefListing.zone = db.relationship(
    "WashingtonZones",
    back_populates="brief_listings",
    lazy=True
)

WashingtonZones.brief_listings = db.relationship(
    "BriefListing",
    back_populates="zone",
    lazy=True
)

WashingtonZones.city = db.relationship('WashingtonCities', back_populates='interests')
#
WashingtonZones.interests = db.relationship('CustomerZone', back_populates='zone')

WashingtonZones.zone_stats_cache = db.relationship('ZoneStatsCache', back_populates='zone')
#
CustomerZone.zone = db.relationship("WashingtonZones",   back_populates="interests")

CustomerZone.customer = db.relationship('Customer', back_populates='zones')

ZoneStatsCache.zone = db.relationship('WashingtonZones', back_populates='zone_stats_cache')

WashingtonCities.interests = db.relationship('WashingtonZones', back_populates='city')

Customer_property_types = db.Table('Customer_property_types',
    db.Column('user_id', db.Integer, db.ForeignKey('Customer.id'), primary_key=True),
    db.Column('property_type_id', db.Integer, db.ForeignKey('property_types.id'), primary_key=True)
)

Customer.property_types = db.relationship('PropertyType', secondary=Customer_property_types,
                                 backref=db.backref('users', lazy='dynamic'))

# Customer to Descriptions
Customer.descriptions = db.relationship('CustomerDescription', back_populates='customer', cascade="all, delete")

CustomerDescription.customer = db.relationship('Customer', back_populates='descriptions')

# BriefListings to PropertyListings

BriefListing.property_listing = db.relationship("PropertyListing", back_populates="brief_listing", uselist=False, cascade="all, delete")

PropertyListing.brief_listing = db.relationship("BriefListing", back_populates="property_listing")

##Investment Cache
BriefListing.cached_investments = db.relationship("CachedInvestmentData", back_populates="brief_listing")
CachedInvestmentData.brief_listing = db.relationship("BriefListing", back_populates="cached_investments")

CachedInvestmentData.customer = db.relationship("Customer", back_populates="cached_investments")
Customer.cached_investments = db.relationship("CachedInvestmentData", back_populates="customer")

Customer.customertype = db.relationship('CustomerType', back_populates='customers')
CustomerType.customers =  db.relationship("Customer", back_populates="customertype")

Customer.maincity = db.relationship('WashingtonCities', back_populates='customers')
WashingtonCities.customers = db.relationship('Customer', back_populates='maincity')