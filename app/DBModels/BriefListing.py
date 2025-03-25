from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric

from app.config import RECENTLYSOLD, LIKELYSOLDWITHOUTAGENTS, OTHER, AUCTIONITEM, FOR_RENT

Base = declarative_base()
from app.extensions import db
from datetime import datetime, timedelta
from app.useful_func import safe_float_conversion,safe_int_conversion
import decimal
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
# from app.DBModels.CustomerZpid import CustomerZpid
# from app.models.brief_listing import BriefListing


def is_equal_with_tolerance(val1, val2, tolerance=1e-4):
    return abs(val1 - val2) <= tolerance

def hasDrivewayParkingFromPropertyData(propertydata):
    try:
        if propertydata['resoFacts']['parkingFeatures'] is None:
            return None
    except:
        print(f'Cannot Find Parking Features Information for {propertydata["abbreviatedAddress"]}')
        return None
    hasDrivewayParking = False
    for feature in propertydata['resoFacts']['parkingFeatures']:
        if feature =='Driveway':
            hasDrivewayParking = True
            return hasDrivewayParking
    return hasDrivewayParking



class BriefListing(db.Model):
    __tablename__= 'BriefListing'

    zpid = db.Column(db.BigInteger, primary_key=True, nullable=True)
    NWMLS_id = db.Column(db.Integer, nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('WashingtonZones.id'), nullable=True)
    bathrooms = db.Column(db.Float, nullable=True, default=1.0)
    bedrooms = db.Column(db.Float, nullable=True, default=1.0)
    city = db.Column(db.String(255), nullable=True)  # Specify length here
    country = db.Column(db.String(255), nullable=True)
    # currency = db.Column(db.String(10), nullable=True)
    dateSold = db.Column(BigInteger, nullable=True)
    soldtime = db.Column(BigInteger, nullable=True)
    daysOnZillow = db.Column(db.Integer, nullable=True)
    homeStatus = db.Column(db.String(100), nullable=True)
    homeStatusForHDP = db.Column(db.String(100), nullable=True)
    homeType = db.Column(db.String(100), nullable=True)
    imgSrc = db.Column(db.String(255), nullable=True)
    isFeatured = db.Column(db.Boolean, nullable=True)
    description = db.Column(Text, nullable=True)
    # isNonOwnerOccupied = db.Column(db.Boolean, nullable=True)
    isPreforeclosureAuction = db.Column(db.Boolean, nullable=True)
    isPremierBuilder = db.Column(db.Boolean, nullable=True)
    isShowcaseListing = db.Column(db.Boolean, nullable=True)
    isUnmappable = db.Column(db.Boolean, nullable=True)
    isZillowOwned = db.Column(db.Boolean, nullable=True)
    latitude = db.Column(Numeric(precision=10,scale=7), nullable=True)
    livingArea = db.Column(db.Float, nullable=True)
    longitude = db.Column(Numeric(precision=10,scale=7), nullable=True)
    price = db.Column(db.BigInteger, nullable=True)
    soldprice = db.Column(db.Integer, nullable=True)
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
    lpctime = db.Column(BigInteger, nullable=True)# latest price change time
    soldBy = db.Column(db.String(100), nullable=True)
    waybercomments = db.Column(db.String(255), nullable=True)
    openhouseneed = db.Column(db.Boolean,nullable=True)
    outsideZones = db.Column(db.Boolean, nullable=True, default=False)
    parkingSpaces = db.Column(db.Integer, nullable=True)
    yearBuilt = db.Column(db.Integer, nullable=True)
    yearBuiltEffective = db.Column(db.Integer, nullable=True)
    hasDrivewayParking = db.Column(db.Boolean, nullable=True)
    # Define the one-to-one relationship to FSBOStatus
    # zone = db.relationship('WashingtonZones', backref='brief_listings', lazy=True)
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
        return f"{self.streetAddress}, {self.city} {self.zipcode}, NWMLS {self.NWMLS_id}, zpid: {self.zpid}"

    def updateListingLength(self,listinglength):
        self.list2penddays=listinglength['list2penddays']
        self.list2solddays = listinglength['list2solddays']
        self.listprice = listinglength['listprice']
        self.soldprice = listinglength['soldprice']

        if self.soldprice is not None and self.listprice is not None:
            self.pricedelta=self.soldprice-self.listprice

    def __str__(self):
        return self.ref_address()

    def __repr__(self):
        return self.ref_address()

    def to_dict(self):
        return {
            'zpid': self.zpid,
            'streetAddress': self.streetAddress,
            'city': self.city,
            'state': self.state,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'livingArea': self.livingArea,
            'price': self.price,
            'soldBy': self.soldBy,
            'homeStatus': self.homeStatus,
            'neighbourhood': self.neighbourhood,
            'soldtime': self.soldtime,
            'waybercomments':self.waybercomments,
            'fsbostatus': self.fsbo_status,
            'bathrooms': self.bathrooms,
            'bedrooms': self.bedrooms,
            'hdpUrl': self.hdpUrl,
            'imgSrc': self.imgSrc,
            'doz': self.daysOnZillow,
            'list2penddays':self.list2penddays,
            'zone_id': self.zone_id
        }

    def getPropertyData(self):
        propertydata = loadPropertyDataFromBrief(self)
        listresults = ListingLengthbyBriefListing(propertydata)
        self.updateListingLength(listresults)
        try:
            self.hdpUrl = propertydata['hdpUrl']
            self.description = propertydata['description']
            self.yearBuilt = propertydata.get('yearBuilt', 'Missing')
            self.yearBuiltEffective = propertydata.get('yearBuiltEffective', 'Missing')
            self.hasDrivewayParking = hasDrivewayParkingFromPropertyData(propertydata)
        except Exception as e:
            print(e, self, 'Failed to get hdpurl')
        try:
            if 'parking' in propertydata['resoFacts'].keys():
                self.parkingSpaces = propertydata['resoFacts']['parking']
            elif 'parkingCapacity' in propertydata['resoFacts'].keys():
                self.parkingSpaces = propertydata['resoFacts']['parkingCapacity']
        except Exception as e:
            print(e, self, 'Failed to get parking spaces')

        if self.soldprice is not None:
            self.soldprice = propertydata['lastSoldPrice']
        try:
            self.NWMLS_id = propertydata['attributionInfo']['mlsId']
            print(propertydata['attributionInfo']['mlsName'])
            if "RMLS (OR)"==propertydata['attributionInfo']['mlsName']:
                self.waybercomments = "RMLS (OR)"

            if "SMLS"==propertydata['attributionInfo']['mlsName']:
                self.waybercomments = "SMLS"

            if "Zillow Rentals" == propertydata['attributionInfo']['mlsName']:
                self.waybercomments = "Zillow Rentals"

            if self.NWMLS_id is None:
                # if propertydata['attributionInfo']:
                #     self.homeStatus == 'ForRent'
                if propertydata['attributionInfo']['agentName'] is None and propertydata['homeStatus'] in [RECENTLYSOLD, OTHER, 'SOLD'] :
                    self.waybercomments=LIKELYSOLDWITHOUTAGENTS
                    print('no mls id!!', LIKELYSOLDWITHOUTAGENTS)
                elif 'agentName' in propertydata['attributionInfo'].keys():
                    if 'auction' in propertydata['attributionInfo']['agentName'].lower():
                        self.waybercomments = AUCTIONITEM
                        print('no mls id!!', AUCTIONITEM)
                else:
                    print('No MLS id!! ' ,  propertydata['attributionInfo'])
        except Exception as e:
            print(e, self, 'Failed getting NWMLS ID')
        print(self)
        return propertydata



    def isBriefListingInZone(self,WA_geojson_features):
        if self.latitude is not None and self.longitude is not None:
            for feature in WA_geojson_features:
                if feature['geometry']['coordinates'][0] == self.longitude and feature['geometry']['coordinates'][1] == self.latitude:
                    return True
        return False


    def needsUpdate(self, newBrieflisting):
        needs_update = False
        updatereason = ''
        gapis_neighbourhood = get_neighborhood(newBrieflisting.latitude, newBrieflisting.longitude)
        newBrieflisting.gapis_neighbourhood = gapis_neighbourhood

        for attr in vars(newBrieflisting):
            if attr == '_sa_instance_state':
                continue
            if attr == 'daysOnZillow':
                continue
            if attr == 'listtime':
                if not is_equal_with_tolerance(existing_value, new_value, 100):
                    needs_update = True
                    updatereason = updatereason + ',' + attr + ' value update'
                    break
                continue
            if hasattr(self, attr):
                existing_value = getattr(self, attr)
                new_value = getattr(self, attr)
                if isinstance(existing_value, decimal.Decimal) and isinstance(new_value, decimal.Decimal):
                    # For float values, use the tolerance-based comparison
                    if not is_equal_with_tolerance(existing_value, new_value):
                        needs_update = True
                        updatereason = updatereason + ',' + attr + ' value update'
                        break
                elif isinstance(existing_value, float) and isinstance(new_value, float):
                    # For float values, use the tolerance-based comparison
                    if not is_equal_with_tolerance(existing_value, new_value, 0.1):
                        needs_update = True
                        updatereason = updatereason + ',' + attr + ' value update'
                        break

                elif attr == 'homeStatus':
                    if not existing_value == new_value:
                        needs_update = True
                        updatereason = updatereason + ',' + attr + 'from ' + self.__str__() + ' to ' + new_value
                elif existing_value != new_value:
                    # For all other data types, use standard comparison
                    needs_update = True
                    updatereason = updatereason + ',' + attr + ' value update'
                    break
        return needs_update, updatereason




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
            new_listing.soldtime = safe_int_conversion(
                briefhomedata.get('dateSold', 0))/1000
            new_listing.daysOnZillow = safe_int_conversion(briefhomedata.get('daysOnZillow', 0))
            new_listing.homeStatus = briefhomedata.get('homeStatus', 'Missing')
            new_listing.homeStatusForHDP = briefhomedata.get('homeStatusForHDP', 'Missing')
            new_listing.homeType = briefhomedata.get('homeType', 'Missing')
            new_listing.imgSrc = briefhomedata.get('imgSrc', 'Missing')
            new_listing.isFeatured = briefhomedata.get('isFeatured', False)
            # new_listing.isNonOwnerOccupied = briefhomedata.get('isNonOwnerOccupied', False)
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

    @classmethod
    def CreateBriefListingFromPropertyData(cls, propertydata,neighbourhood, zillowapi_neighbourhood, search_neigh):
        try:
            new_listing = cls()
            new_listing.zpid = propertydata.get('zpid')
            new_listing.neighbourhood = neighbourhood
            new_listing.zillowapi_neighbourhood = zillowapi_neighbourhood
            new_listing.search_neigh = search_neigh
            new_listing.bathrooms = safe_float_conversion(propertydata.get('bathrooms', 1.0))
            new_listing.bedrooms = safe_float_conversion(propertydata.get('bedrooms', 1.0))
            new_listing.city = propertydata.get('city', 'Missing')
            new_listing.country = propertydata.get('country', 'Missing')
            # new_listing.currency = briefhomedata.get('currency', 'Missing')
            new_listing.livingArea=safe_float_conversion(propertydata.get('livingArea', 1.0))
            new_listing.dateSold = safe_int_conversion(
                propertydata.get('dateSold', 0))  # Consider datetime conversion if necessary
            new_listing.soldtime = safe_int_conversion(
                propertydata.get('dateSold', 0))/1000
            new_listing.daysOnZillow = safe_int_conversion(propertydata.get('daysOnZillow', 0))
            new_listing.homeStatus = propertydata.get('homeStatus', 'Missing')
            new_listing.homeStatusForHDP = propertydata.get('homeStatusForHDP', 'Missing')
            new_listing.homeType = propertydata.get('homeType', 'Missing')
            new_listing.imgSrc = propertydata.get('imgSrc', 'Missing')
            new_listing.description = propertydata.get('description', 'Missing')
            new_listing.isFeatured = propertydata.get('isFeatured', False)
            # new_listing.isNonOwnerOccupied = propertydata.get('isNonOwnerOccupied', False)
            new_listing.isPreforeclosureAuction = propertydata.get('isPreforeclosureAuction', False)
            new_listing.isPremierBuilder = propertydata.get('isPremierBuilder', False)
            new_listing.isShowcaseListing = propertydata.get('isShowcaseListing', False)
            new_listing.isUnmappable = propertydata.get('isUnmappable', False)
            new_listing.isZillowOwned = propertydata.get('isZillowOwned', False)
            new_listing.latitude = decimal.Decimal(propertydata.get('latitude', '0.0000000'))
            new_listing.longitude = decimal.Decimal(propertydata.get('longitude', '0.0000000'))
            new_listing.price = safe_int_conversion(propertydata.get('price', 0))
            new_listing.state = propertydata.get('state', 'Missing')
            new_listing.streetAddress = propertydata.get('streetAddress', 'Missing')
            new_listing.zipcode = propertydata.get('zipcode', 'Missing')
            new_listing.list2penddays = safe_int_conversion(propertydata.get('list2penddays', 0))
            new_listing.list2solddays = safe_int_conversion(propertydata.get('list2solddays', 0))
            new_listing.listprice = safe_int_conversion(propertydata.get('listprice', 0))
            new_listing.zestimate = safe_int_conversion(propertydata.get('zestimate', 0))
            new_listing.taxAssessedValue = safe_float_conversion(propertydata.get('taxAssessedValue', 0.0))
            new_listing.lotAreaUnit = propertydata.get('lotAreaUnit', 'Missing')
            new_listing.lotAreaValue = safe_float_conversion(propertydata.get('lotAreaValue', 0.0))
            # Assuming `listing_sub_type` is passed as a dictionary and directly assignable
            new_listing.listing_sub_type = propertydata.get('listing_sub_type', {})
            new_listing.rentZestimate = safe_int_conversion(propertydata.get('rentZestimate', 0))
            # Assuming that for optional fields without defaults you want to use None or a sentinel value
            new_listing.unit = propertydata.get('unit', None)  # Handling for 'unit' as optional
            new_listing.videoCount = propertydata.get('videoCount', '0')  # Assuming '0' as default for missing
            # new_listing.isRentalWithBasePrice = briefhomedata.get('isRentalWithBasePrice', False)
            new_listing.newConstructionType = propertydata.get('newConstructionType', 'Missing')
            new_listing.hdpUrl = propertydata.get('hdpUrl', 'Missing')
            new_listing.pricedelta = safe_int_conversion(propertydata.get('pricedelta', 0))
            new_listing.yearBuilt = propertydata.get('yearBuilt', 'Missing')
            new_listing.yearBuiltEffective = propertydata.get('yearBuiltEffective', 'Missing')
            new_listing.hasDrivewayParking =hasDrivewayParkingFromPropertyData(propertydata)
            listing_time = datetime.utcnow() - timedelta(seconds=safe_int_conversion(propertydata.get('timeOnZillow', 0))/1000)
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
    'soldtime': 1708934400,
    'daysOnZillow': 1,
    'homeStatus': 'RECENTLY_SOLD',
    'homeStatusForHDP': 'RECENTLY_SOLD',
    'homeType': 'SINGLE_FAMILY',
    'imgSrc': 'https://photos.zillowstatic.com/fp/a6ad1b1713ff7fb31f4bdf9b9a96d879-p_e.jpg',
    'isFeatured': False,
    # 'isNonOwnerOccupied': True,
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