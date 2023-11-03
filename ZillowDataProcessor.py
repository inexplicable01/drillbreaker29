import requests
PRICEHISTORY = 'priceHistory'

from datetime import datetime
rapidapikey = "0f1a70c877msh63c2699008fda33p17811djsn4ef183cca70a"
from Download_Image import download_image
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

def ListingLength(soldhouse, Listing, db):

    if soldhouse.list2pendCheck==0:
        url = "https://zillow56.p.rapidapi.com/property"
        querystring = {"zpid":soldhouse.zpid}
        headers = {
            "X-RapidAPI-Key": rapidapikey,
            "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        # print(response.json())
        houseresult = response.json()
        if PRICEHISTORY in houseresult.keys():
            soldposs =[]
            for event in houseresult[PRICEHISTORY]:

                if event['event']=='Listed for sale':
                    print(event['date'] + 'Listed for Sale ' + soldhouse.streetAddress)
                    for e in soldposs:
                        if e['event'] == 'Pending sale':
                            print(e['date'] + '  Pending  ' + soldhouse.streetAddress)

                            list2penddays = date_difference(e['date'], event['date'])
                            print(soldhouse.streetAddress + ' Took ' + str(list2penddays) + ' to be UnderContract')
                            soldhouse.list2pend = list2penddays
                            soldhouse.list2pendCheck = 1
                            db.session.commit()
                        if e['event'] == 'Sold':
                            print(e['date'] + '  Sold  ' + soldhouse.streetAddress)
                            print(soldhouse.streetAddress + ' Took ' + str(date_difference(e['date'],event['date']))+ ' to sell')
                    break
                else:
                    soldposs.append(event)
            soldhouse.list2pendCheck = 1
            db.session.commit()
        else:
            print('Lack of History Data for ' + soldhouse.streetAddress)
            soldhouse.list2pendCheck = 1
            db.session.commit()
import os
from os.path import *
def PicturesFromMLS(zpid, Listing, db):

    url = "https://zillow56.p.rapidapi.com/property"
    querystring = {"zpid":zpid}
    headers = {
        "X-RapidAPI-Key": rapidapikey,
        "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    # print(response.json())
    houseresult = response.json()

    if 'photos' in houseresult.keys():
        housename = houseresult['address']['streetAddress'] + ' ' + houseresult['address']['city']
        if not os.path.exists(join(HousePicsDIR,housename)):
            os.mkdir(join(HousePicsDIR,housename))
        for i,el in enumerate(houseresult['photos']):
            url = el['mixedSources']['jpeg'][-1]['url']
            download_image(url, join(HousePicsDIR,housename))
        return True
    return False







# Test the function
# date1 = '2023-01-01'
# date2 = '2023-03-01'
# print(date_difference(date1, date2))  # Output: 59
