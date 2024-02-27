HousePicsDIR = "C:/Users/waich/Dropbox/EstateFlow/DrillBreaker29/HousePics"
from Download_Image import download_image
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID , SearchZillowByAddress , SearchZillowSoldHomesByLocation
from app.ZillowAPI.ZillowAddress import ZillowAddress
from app.ZillowAPI.ZillowBriefHomeData import BriefListing
from os.path import join
import os
import json

PRICEHISTORY = 'priceHistory'
from datetime import datetime


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


def ListingLengthbyBriefListing(brieflisting:BriefListing):

    propertydata = loadPropertyDataFromBrief(brieflisting)
    list2penddays = None
    list2solddays=None
    listprice=None
    try:
        if PRICEHISTORY in propertydata.keys():
            soldposs = []
            for event in propertydata[PRICEHISTORY]:

                if event['event'] == 'Listed for sale':
                    print(event['date'] + 'Listed for Sale ' + propertydata['address']['streetAddress'])
                    listprice = event['price']
                    for e in soldposs:
                        if e['event'] == 'Pending sale':
                            print(e['date'] + '  Pending  ' + propertydata['address']['streetAddress'])
                            list2penddays = date_difference(e['date'], event['date'])
                            print(propertydata['address']['streetAddress']+ ' Took ' + str(list2penddays) + ' to be UnderContract')
                        if e['event'] == 'Sold':
                            list2solddays = date_difference(e['date'], event['date'])
                            print(e['date'] + '  Sold  ' + propertydata['address']['streetAddress'])
                            print(propertydata['address']['streetAddress'] + ' Took ' + str(
                                date_difference(e['date'], event['date'])) + ' to sell')
                    break
                else:
                    soldposs.append(event)
            return {'list2penddays': list2penddays,
                    'list2solddays': list2solddays,
                    'listprice':listprice}
        else:
            return {'list2penddays': None,
                'list2solddays': None,
                    'listprice':listprice}

    except Exception as e:
        print('Lack of History Data for ' + e.__str__())
        return {'list2penddays': None,
                'list2solddays': None,
                'listprice': listprice}


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


def FindSoldHomesByLocation(location, doz):
    soldrawdata = SearchZillowSoldHomesByLocation(location,doz)
    soldhomes = []
    for briefhomedata in soldrawdata:
        soldhomes.append(BriefListing(**briefhomedata))
    return soldhomes



def loadPropertyDataFromBrief(brieflisting:BriefListing):
    filepath = os.path.join(os.getenv('ADDRESSJSON'), brieflisting.ref_address() + '.txt')
    if not os.path.exists(filepath):
        propertydata = SearchZillowByZPID(brieflisting.zpid)
        json_string = json.dumps(propertydata, indent=4)
        with open(filepath, 'w') as f:
            f.write(json_string)
    else:
        with open(filepath, 'r') as file:
            # Read the content of the file
            text_content = file.read()
            propertydata = json.loads(text_content)


            # {
            #     "message": "You have exceeded the rate limit per second for your plan, ULTRA, by the API provider"
            # }
    return propertydata

