PRICEHISTORY = 'priceHistory'

# from app.DataBaseFunc import dbmethods
from app.config import Config
# from app.ZillowAPI.ZillowAPICall import *

HousePicsDIR = "C:/Users/waich/Dropbox/EstateFlow/DrillBreaker29/HousePics"
from Download_Image import download_image
from app.ZillowAPI.ZillowAPICall import SearchZillowNewListingByLocation,\
    SearchZillowByZPID , \
    SearchZillowByAddress , \
    SearchZillowNewListingByInterest,\
    SearchZillowHomesByLocation

# from app.DBModels.BriefListing import BriefListing
from os.path import join
import os
import json

PRICEHISTORY = 'priceHistory'
from datetime import datetime
def date_difference(date1: str, date2: str) -> int:
    # Define the date format
    date_format = "%Y-%m-%d"

    # Convert the string dates to datetime objects
    date1_obj = datetime.strptime(date1, date_format)
    date2_obj = datetime.strptime(date2, date_format)

    # Find the difference between the two dates
    difference = date2_obj - date1_obj

    # Return the number of days
    return abs(difference.days)


# def SearchAllNewListing(location, daysonzillow):
#     houseresult = SearchZillowNewListingByLocation(location, daysonzillow)
#     dbmethods.loadHouseSearchDataintoDB(houseresult, 'forSale')





# def ZillowSearchForOpenHouse(TR,TL,BR,BL):
#
#     location = 'seattle'
#     daysonzillow = 30
#     briefhomedataarr = SearchZillowNewListingByLocation(location,daysonzillow)
#     openbrieflisting=[]
#     for briefhomedata in briefhomedataarr:
#         # filtered_data = filter_dataclass_fields(briefhomedata, BriefListing)
#         openbrieflisting.append(BriefListing.CreateBriefListing(briefhomedata, None, None, location))
#         # soldhomes=  soldhomes+ FindSoldHomesByLocation(location,30)
#
#     filtered_houses = []
#     for brieflisting in openbrieflisting:
#
#         # Check if the house's coordinates fall within the defined bounding box
#         if (BL[0] <= brieflisting.latitude <= TL[0]) and (TL[1] <= brieflisting.longitude <= TR[1]):
#
#             propertydata = loadPropertyDataFromBrief(brieflisting)
#             try:
#                 print('address',propertydata['address']['streetAddress'])
#                 # print('isOpenHouse',response['listingSubType']['isOpenHouse'])
#                 # print('openHouseSchedule',response['openHouseSchedule'])
#                 # print('homeType', response['homeType'])
#                 # print('propertyCondition', response['resoFacts']['propertyCondition'])
#                 # print('neighborhoodRegion', response['neighborhoodRegion'])
#                 # neighborhoodRegion
#                 if propertydata['homeType']=="LOT" or propertydata['homeType']=="MULTI_FAMILY" or propertydata['homeType']=="CONDO":
#                     print('Not a proper home Type, skip')
#                     continue
#                 if propertydata['resoFacts']['propertyCondition']=="Under Construction":
#                     print('Under Construction, skip')
#                     continue
#                 if propertydata['neighborhoodRegion']['name']  in Config.WRONGNEIGHBORHOODS:
#                     print('wrong neighbourhood, skip')
#                     continue
#                 if not propertydata['listingSubType']['isOpenHouse']:
#                     filtered_houses.append(propertydata)
#             except:
#                 continue
#
#     # Calculate the center of your bounding box (average of the bounding box coordinates)
#
#     return filtered_houses
#

# def ZillowSearchForForSaleHomes(clientinterest):
#     forsalehomesarr = []
#     for area in clientinterest['area']:
#         location = area + ' seattle'
#         homesbeingsoldraw = SearchZillowNewListingByInterest(location=location,
#                                                         beds_min=clientinterest['bedrooms_min'],
#                                                         beds_max=clientinterest['bedrooms_max'],
#                                                         baths_min=clientinterest['bathrooms_min'],
#                                                         price_max=clientinterest['pricemax'],
#                                                         daysonzillow=7)
#
#
#     # for forsalebriefdata in forsalehomesarr:
#     #     print(forsalebriefdata)
#     return forsalehomesarr
    # return filtered_houses


# Test the function
# date1 = '2023-01-01'
# date2 = '2023-03-01'
# print(date_difference(date1, date2))  # Output: 59
def PicturesFromMLS(zpid):
    houseresult = SearchZillowByZPID(zpid)

    if 'photos' in houseresult.keys():
        housename = houseresult['address']['streetAddress'] + ' ' + houseresult['address']['city']
        if not os.path.exists(join(HousePicsDIR, housename)):
            os.mkdir(join(HousePicsDIR, housename))
        for i, el in enumerate(houseresult['photos']):
            url = el['mixedSources']['jpeg'][-1]['url']
            download_image(url, join(HousePicsDIR, housename))
        return True
    return False

from datetime import datetime
def ListingLengthbyBriefListing(propertydata):
    date_format = "%Y-%m-%d"
    list2penddays = None
    list2solddays=None
    listprice=None
    listdate = None
    penddate=None
    solddate=None
    soldprice=None
    try:
        if PRICEHISTORY in propertydata.keys():
            soldposs = []
            for event in propertydata[PRICEHISTORY]:

                if event['event'] == 'Listed for sale':
                    # print(event['date'] + 'Listed for Sale ' + propertydata['address']['streetAddress'])
                    listprice = event['price']
                    listdate = datetime.strptime(event['date'], date_format)
                    for e in soldposs:
                        if e['event'] == 'Pending sale':
                            # print(e['date'] + '  Pending  ' + propertydata['address']['streetAddress'])
                            list2penddays = date_difference(e['date'], event['date'])
                            penddate = datetime.strptime(e['date'], date_format)
                            # print(propertydata['address']['streetAddress']+ ' Took ' + str(list2penddays) + ' to be UnderContract')
                        if e['event'] == 'Sold':
                            list2solddays = date_difference(e['date'], event['date'])
                            solddate = datetime.strptime(e['date'], date_format)
                            soldprice = e['price']
                            # print(e['date'] + '  Sold  ' + propertydata['address']['streetAddress'])
                            # print(propertydata['address']['streetAddress'] + ' Took ' + str(
                            #     date_difference(e['date'], event['date'])) + ' to sell')
                    break
                else:
                    soldposs.append(event)
            return {'list2penddays': list2penddays,
                    'list2solddays': list2solddays,
                    'listprice':listprice,
                    'listdate': listdate,
                    'penddate': penddate,
                    'solddate': solddate,
                    'soldprice': soldprice
                    }
        else:
            return {'list2penddays': list2penddays,
                'list2solddays': list2solddays,
                    'listprice':listprice,
                    'listdate':listdate,
                    'penddate':penddate,
                    'solddate':solddate,
                    'soldprice':soldprice
                    }

    except Exception as e:
        print('Lack of History Data for ' + e.__str__())
        return {'list2penddays': list2penddays,
                'list2solddays': list2solddays,
                    'listprice':listprice,
                    'listdate':listdate,
                    'penddate':penddate,
                    'solddate':solddate,
                    'soldprice':soldprice
                    }


def date_difference(date1: str, date2: str) -> int:
    # Define the date format
    date_format = "%Y-%m-%d"
    # Convert the string dates to datetime objects
    date1_obj = datetime.strptime(date1, date_format)
    date2_obj = datetime.strptime(date2, date_format)
    # Find the difference between the two dates
    difference = date2_obj - date1_obj
    # Return the number of days
    return abs(difference.days)

def ListingStatus(brieflisting):
    propertydetails = SearchZillowByZPID(brieflisting.zpid)
    return propertydetails['homeStatus']


def loadPropertyDataFromAddress(fileaddress):
    filepath = os.path.join(os.getenv('ADDRESSJSON'), fileaddress + '.txt')
    if not os.path.exists(filepath):
        propertydata = SearchZillowByAddress(fileaddress)
        json_string = json.dumps(propertydata, indent=4)
        with open(filepath, 'w') as f:
            f.write(json_string)
    else:
        with open(filepath, 'r') as file:
            # Read the content of the file
            text_content = file.read()
            propertydata = json.loads(text_content)
    return propertydata


def savePropertyData(propertydata):
    addressStr = propertydata['address']['streetAddress'] + '  ' + \
                 propertydata['address']['city'] + ' ' + \
                 propertydata['address']['zipcode']

    filepath = os.path.join(os.getenv('ADDRESSJSON'), addressStr + '.txt')
    if not os.path.exists(filepath):
        json_string = json.dumps(propertydata, indent=4)
        with open(filepath, 'w') as f:
            f.write(json_string)



# def FindHomesByNeighbourhood(search_neigh, doz):
#     interval=100
#     minhomesize=4000
#     maxhomesize=interval+minhomesize
#     soldbrieflistingarr = []
#     while maxhomesize < 6000:
#         soldrawdata = SearchZillowHomesByLocation(search_neigh,status="recentlySold",doz=doz,minhomesize=minhomesize,maxhomesize=maxhomesize)
#         for briefhomedata in soldrawdata:
#                 soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None,None,search_neigh))
#         print(f"Finished searching {minhomesize} to {maxhomesize}")
#         minhomesize = minhomesize + interval
#         maxhomesize = maxhomesize + interval
#     forsalerawdata = SearchZillowHomesByLocation(search_neigh,status="forSale",duration="any")
#     forsalebrieflistingarr = []
#     for briefhomedata in forsalerawdata:
#             forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None,None,search_neigh))
#     return soldbrieflistingarr,forsalebrieflistingarr


def loadPropertyDataFromBrief(brieflisting):

    # print('Load property : ',brieflisting)
    propertydata = SearchZillowByZPID(brieflisting.zpid)

    return propertydata
