HousePicsDIR = "C:/Users/waich/Dropbox/EstateFlow/DrillBreaker29/HousePics"
from Download_Image import download_image
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID
from os.path import join
import os

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


def ListingLengthbyZPID(zpid):
    houseresult = SearchZillowByZPID(zpid)
    list2penddays = None
    list2solddays=None
    listprice=None
    try:
        if PRICEHISTORY in houseresult.keys():
            soldposs = []
            for event in houseresult[PRICEHISTORY]:

                if event['event'] == 'Listed for sale':
                    print(event['date'] + 'Listed for Sale ' + houseresult['address']['streetAddress'])
                    listprice = event['price']
                    for e in soldposs:
                        if e['event'] == 'Pending sale':
                            print(e['date'] + '  Pending  ' + houseresult['address']['streetAddress'])
                            list2penddays = date_difference(e['date'], event['date'])
                            print(houseresult['address']['streetAddress']+ ' Took ' + str(list2penddays) + ' to be UnderContract')
                        if e['event'] == 'Sold':
                            list2solddays = date_difference(e['date'], event['date'])
                            print(e['date'] + '  Sold  ' + houseresult['address']['streetAddress'])
                            print(houseresult['address']['streetAddress'] + ' Took ' + str(
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
        print('Lack of History Data for ' + e)
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
