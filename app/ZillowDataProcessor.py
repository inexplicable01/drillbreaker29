import requests
PRICEHISTORY = 'priceHistory'

from datetime import datetime
from app.DataBaseFunc import dbmethods
from app.config import Config
from app.ZillowAPI.ZillowAPICall import *

HousePicsDIR = "C:/Users/waich/Dropbox/EstateFlow/DrillBreaker29/HousePics"

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

# def ListingLength(soldhouse, Listing, db):
#
#     if soldhouse.list2pendCheck==0:
#         url = "https://zillow56.p.rapidapi.com/property"
#         querystring = {"zpid":soldhouse.zpid}
#         headers = {
#             "X-RapidAPI-Key": rapidapikey,
#             "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
#         }
#         response = requests.get(url, headers=headers, params=querystring)
#         # print(response.json())
#         houseresult = response.json()
#         if PRICEHISTORY in houseresult.keys():
#             soldposs =[]
#             for event in houseresult[PRICEHISTORY]:
#
#                 if event['event']=='Listed for sale':
#                     print(event['date'] + 'Listed for Sale ' + soldhouse.streetAddress)
#                     for e in soldposs:
#                         if e['event'] == 'Pending sale':
#                             print(e['date'] + '  Pending  ' + soldhouse.streetAddress)
#
#                             list2penddays = date_difference(e['date'], event['date'])
#                             print(soldhouse.streetAddress + ' Took ' + str(list2penddays) + ' to be UnderContract')
#                             soldhouse.list2pend = list2penddays
#                             soldhouse.list2pendCheck = 1
#                             db.session.commit()
#                         if e['event'] == 'Sold':
#                             print(e['date'] + '  Sold  ' + soldhouse.streetAddress)
#                             print(soldhouse.streetAddress + ' Took ' + str(date_difference(e['date'],event['date']))+ ' to sell')
#                     break
#                 else:
#                     soldposs.append(event)
#             soldhouse.list2pendCheck = 1
#             db.session.commit()
#         else:
#             print('Lack of History Data for ' + soldhouse.streetAddress)
#             soldhouse.list2pendCheck = 1
#             db.session.commit()

def SearchAllNewListing(location, daysonzillow):
    houseresult = SearchZillowNewListingByLocation(location, daysonzillow)
    dbmethods.loadHouseSearchDataintoDB(houseresult, 'forSale')

def ZillowSearchForOpenHouse(TR,TL,BR,BL):

    location = 'seattle'
    daysonzillow = 30
    houseresult = SearchZillowNewListingByLocation(location,daysonzillow)


    filtered_houses = []
    for house in houseresult:

        # Check if the house's coordinates fall within the defined bounding box
        if (BL[0] <= house['latitude'] <= TL[0]) and (TL[1] <= house['longitude'] <= TR[1]):

            response = SearchZillowByZPID(house['zpid'])

            print('address',response['address']['streetAddress'])
            print('isOpenHouse',response['listingSubType']['isOpenHouse'])
            print('openHouseSchedule',response['openHouseSchedule'])
            print('homeType', response['homeType'])
            print('propertyCondition', response['resoFacts']['propertyCondition'])
            print('neighborhoodRegion', response['neighborhoodRegion'])
            # neighborhoodRegion
            if response['homeType']=="LOT" or response['homeType']=="MULTI_FAMILY" or response['homeType']=="CONDO":
                print('Not a proper home Type, skip')
                continue
            if response['resoFacts']['propertyCondition']=="Under Construction":
                print('Under Construction, skip')
                continue
            if response['neighborhoodRegion']['name']  in Config.WRONGNEIGHBORHOODS:
                print('wrong neighbourhood, skip')
                continue


            if not response['listingSubType']['isOpenHouse']:
                filtered_houses.append(response)


    # Calculate the center of your bounding box (average of the bounding box coordinates)

    return filtered_houses





# Test the function
# date1 = '2023-01-01'
# date2 = '2023-03-01'
# print(date_difference(date1, date2))  # Output: 59
