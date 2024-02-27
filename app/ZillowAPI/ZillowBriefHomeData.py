from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class BriefListing:
    bathrooms: Optional[float] = None
    bedrooms: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    dateSold: Optional[int] = None
    daysOnZillow: Optional[int] = None
    homeStatus: Optional[str] = None
    homeStatusForHDP: Optional[str] = None
    homeType: Optional[str] = None
    imgSrc: Optional[str] = None
    isFeatured: Optional[bool] = None
    isNonOwnerOccupied: Optional[bool] = None
    isPreforeclosureAuction: Optional[bool] = None
    isPremierBuilder: Optional[bool] = None
    isShowcaseListing: Optional[bool] = None
    isUnmappable: Optional[bool] = None
    isZillowOwned: Optional[bool] = None
    latitude: Optional[float] = None
    livingArea: Optional[float] = None
    longitude: Optional[float] = None
    price: Optional[float] = None
    priceForHDP: Optional[float] = None
    shouldHighlight: Optional[bool] = None
    state: Optional[str] = None
    streetAddress: Optional[str] = None
    timeOnZillow: Optional[int] = None
    zipcode: Optional[str] = None
    zpid: Optional[int] = None
    list2penddays: Optional[int] = None
    list2solddays: Optional[int] = None
    listprice: Optional[int] = None
    zestimate: Optional[int] = None
    taxAssessedValue: Optional[float] = None
    lotAreaUnit: Optional[str] = None
    lotAreaValue: Optional[float] = None
    listing_sub_type: Optional[Dict] = field(default_factory=dict)
    rentZestimate: Optional[int] = None
    unit: Optional[str] = None
    videoCount: Optional[str] = None
    isRentalWithBasePrice: Optional[bool] = None
    newConstructionType: Optional[str] = None
    hdpUrl: Optional[str] = None


    def ref_address(self):
        return f"{self.streetAddress}_{self.city}_{self.zipcode}".replace(' ', '_')

    def updateListingLength(self,listinglength):
        self.list2penddays=listinglength['list2penddays']
        self.list2solddays = listinglength['list2solddays']
        self.listprice = listinglength['listprice']



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

property_details = BriefListing(**response)
print(property_details)
