from flask import Blueprint, render_template,jsonify, redirect, url_for, request
from flask import Blueprint, redirect, url_for
# from app.RouteModel.EmailModel import sendEmailwithListingforclient
from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForForSaleHomes,loadPropertyDataFromBrief
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.ZillowAPI.ZillowAPICall import *
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import numpy as np
import random
hothomes_bp = Blueprint('hothomes_bp', __name__,url_prefix='/hothomes')
@hothomes_bp.route('/ballard', methods=['GET'])
def showHotHomes():
    neighbourhoods=['Fremont','Ballard','Wallingford']
    selectedhometypes=['SINGLE_FAMILY', 'TOWNHOUSE','CONDO' ]
    unfiltered_forsale=brieflistingcontroller.ForSaleListingsByNeighbourhoodsAndHomeTypes(neighbourhoods, selectedhometypes, 30, 'FOR_SALE')
    # for forsalehome in unfiltered_forsale:
    #     print(forsalehome)
    competivenessoption=['Low', 'A few offers', 'Bidding War']
    infodump = []
    house_c=0
    for house in unfiltered_forsale:
        if house_c>5:
            break
        images=[]
        count = 0
        listingdetails = SearchZillowByZPID(house.zpid)
        if not listingdetails:
            continue
        try:
            if listingdetails['address']['city']!='Seattle':
                continue

            for photo in listingdetails['photos']:
                for jpeg in photo['mixedSources']['jpeg']:
                    if jpeg['width']==384:
                        images.append({
                            "url": jpeg['url'], "caption": photo['caption']
                        })
                        # count = count +1
                # if count>2:
                #     break
            estimatelistingdays = int(round(np.random.normal(7, 5)))
            estimatesoldprice = house.price+100000
            competitiveness =random.choice(competivenessoption)
            infodump.append(
                (listingdetails,house.zpid,images, house, estimatelistingdays,estimatesoldprice ,competitiveness)
            )
            house_c+=1

        except Exception as e:
            print(e)
    return render_template('HotHomes.html', infodump=infodump)

@hothomes_bp.route('/ballard', methods=['POST'])
def getUpdatedHomes():

    clientinterest={
        'area':['Fremont','Ballard','Wallingford'],
        'bedrooms_min':1,
        'bedrooms_max': 4,
        'bathrooms_min':1.5,
        'pricemax': 1700000
    }
    forsalebriefdata = ZillowSearchForForSaleHomes(clientinterest)

    for brieflisting in forsalebriefdata:

        try:
            propertydata = loadPropertyDataFromBrief(brieflisting)
            brieflisting.hdpUrl = propertydata['hdpUrl']
        except Exception as e:
            print(e, brieflisting)

    changebrieflistingarr,oldbrieflistingarr=brieflistingcontroller.SaveBriefListingArr(forsalebriefdata)

    return render_template('HotHomes.html')
# @openhouse_bp.route('/showopenhouseopportunity', methods=['GET','POST'])
# def SearchForOpenHouseRoute():
#     map_html = SearchForOpenHouses()
#     return render_template('OpenHouse.html', m=map_html)