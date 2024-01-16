import os
import json
from app.ZillowSearch import SearchProperty

with open('keystoremove.txt', 'r') as file:
    keys_to_delete = [line.strip() for line in file]
class ZillowAddress():

    def __init__(self, address,bathrooms=None,bedrooms=None,description=None,city=None,
                 cityId=None,comps=None,
    country=None,
    county=None,
    countyId=None,
    dateSold=None,
    daysOnZillow=None,
    floorMaps=None,
    homeType=None,
    homeValues=None,
    hugePhotos=None,
    isIncomeRestricted=None,
    isListedByOwner=None,
    keystoneHomeStatus=None,
    lastSoldPrice=None,
    latitude=None,
    listPriceLow=None,
    listingMetadata=None,
    listingSubType=None,
    livingArea=None,
    longitude=None,
    lotSize=None,
    monthlyHoaFee=None,
    nearbyCities=None,
    nearbyHomes=None,
    nearbyNeighborhoods=None,
    nearbyZipcodes=None,
    neighborhoodRegion=None,
    newConstructionType=None,
    onsiteMessage=None,
    parcelId=None,
    photos=None,
    price=None,
    priceHistory=None,
    propertyTaxRate=None,
    rentZestimate=None,
    resoFacts=None,
    restimateHighPercent=None,
    restimateLowPercent=None,
    schools=None,
    state=None,
    stateId=None,
    taxAssessedValue=None,
    taxAssessedYear=None,
    taxHistory=None,
    timeOnZillow=None,
    timeZone=None,
    yearBuilt=None,
    zestimate=None,
    zestimateHighPercent=None,
    zestimateLowPercent=None,
    ):
        self.address = address
        self.bathrooms = bathrooms
        self.bedrooms = bedrooms
        self.city =                                 city
        self.cityId =                                cityId
        self.comps =                                 comps
        self.country =                              country
        self.county =                               county
        self.countyId =                             countyId
        self.dateSold =                             dateSold
        self.daysOnZillow =                          daysOnZillow
        self.description =                           description
        self.floorMaps =                             floorMaps
        self.homeType =                              homeType
        self.homeValues =                            homeValues
        self.hugePhotos =                            hugePhotos
        self.isIncomeRestricted =                    isIncomeRestricted
        self.isListedByOwner =                       isListedByOwner
        self.keystoneHomeStatus =                    keystoneHomeStatus
        self.lastSoldPrice =                         lastSoldPrice
        self.latitude =                              latitude
        self.listPriceLow =                          listPriceLow
        self.listingMetadata =                       listingMetadata
        self.listingSubType =                        listingSubType
        self.livingArea =                            livingArea
        self.longitude =                             longitude
        self.lotSize =                               lotSize
        self.monthlyHoaFee =                         monthlyHoaFee
        self.nearbyCities =                          nearbyCities
        self.nearbyHomes =                           nearbyHomes
        self.nearbyNeighborhoods =                   nearbyNeighborhoods
        self.nearbyZipcodes =                        nearbyZipcodes
        self.neighborhoodRegion =                    neighborhoodRegion
        self.newConstructionType =                   newConstructionType
        self.onsiteMessage =                         onsiteMessage
        self.parcelId =                              parcelId
        self.photos = 								 photos
        self.price = 								 price
        self.priceHistory = 						 priceHistory
        self.propertyTaxRate = 						 propertyTaxRate
        self.rentZestimate =                         rentZestimate
        self.resoFacts =                             resoFacts
        self.restimateHighPercent =                  restimateHighPercent
        self.restimateLowPercent =                   restimateLowPercent
        self.schools =                               schools
        self.state =                                 state
        self.stateId =                               stateId
        self.taxAssessedValue =                      taxAssessedValue
        self.taxAssessedYear =                       taxAssessedYear
        self.taxHistory =                            taxHistory
        self.timeOnZillow =                          timeOnZillow
        self.timeZone =                              timeZone
        self.yearBuilt =                             yearBuilt
        self.zestimate =                             zestimate
        self.zestimateHighPercent =                  zestimateHighPercent
        self.zestimateLowPercent =            zestimateLowPercent

    @classmethod
    def OpenAddresstxt(cls, fileaddress):
        filepath = os.path.join('addressjson',fileaddress+'.txt')
        if not os.path.exists(filepath):
            propertydata = SearchProperty(fileaddress)
            json_string = json.dumps(propertydata, indent=4)
            with open(filepath, 'w') as f:
                f.write(json_string)
        else:
            with open(filepath, 'r') as file:
                # Read the content of the file
                text_content = file.read()
                propertydata = json.loads(text_content)

        for key in keys_to_delete:
            if key in propertydata:
                del propertydata[key]
        return cls(address = propertydata['address'],
bathrooms = propertydata['bathrooms'],
bedrooms = propertydata['bedrooms'],
city = propertydata['city'],
cityId = propertydata['cityId'],
comps = propertydata['comps'],
country = propertydata['country'],
county = propertydata['county'],
countyId = propertydata['countyId'],
dateSold = propertydata['dateSold'],
daysOnZillow = propertydata['daysOnZillow'],
description = propertydata['description'],
floorMaps = propertydata['floorMaps'],
homeType = propertydata['homeType'],
homeValues = propertydata['homeValues'],
hugePhotos = propertydata['hugePhotos'],
isIncomeRestricted = propertydata['isIncomeRestricted'],
isListedByOwner = propertydata['isListedByOwner'],
keystoneHomeStatus = propertydata['keystoneHomeStatus'],
lastSoldPrice = propertydata['lastSoldPrice'],
latitude = propertydata['latitude'],
listPriceLow = propertydata['listPriceLow'],
listingMetadata = propertydata['listingMetadata'],
listingSubType = propertydata['listingSubType'],
livingArea = propertydata['livingArea'],
longitude = propertydata['longitude'],
lotSize = propertydata['lotSize'],
monthlyHoaFee = propertydata['monthlyHoaFee'],
nearbyCities = propertydata['nearbyCities'],
nearbyHomes = propertydata['nearbyHomes'],
nearbyNeighborhoods = propertydata['nearbyNeighborhoods'],
nearbyZipcodes = propertydata['nearbyZipcodes'],
neighborhoodRegion = propertydata['neighborhoodRegion'],
newConstructionType = propertydata['newConstructionType'],
onsiteMessage = propertydata['onsiteMessage'],
parcelId = propertydata['parcelId'],
photos = propertydata['photos'],
price = propertydata['price'],
priceHistory = propertydata['priceHistory'],
propertyTaxRate = propertydata['propertyTaxRate'],
rentZestimate = propertydata['rentZestimate'],
resoFacts = propertydata['resoFacts'],
restimateHighPercent = propertydata['restimateHighPercent'],
restimateLowPercent = propertydata['restimateLowPercent'],
schools = propertydata['schools'],
state = propertydata['state'],
stateId = propertydata['stateId'],
taxAssessedValue = propertydata['taxAssessedValue'],
taxAssessedYear = propertydata['taxAssessedYear'],
taxHistory = propertydata['taxHistory'],
timeOnZillow = propertydata['timeOnZillow'],
timeZone = propertydata['timeZone'],
yearBuilt = propertydata['yearBuilt'],
zestimate = propertydata['zestimate'],
zestimateHighPercent = propertydata['zestimateHighPercent'],
zestimateLowPercent = propertydata['zestimateLowPercent'])

    def printdetails(self):
        print(self.address)