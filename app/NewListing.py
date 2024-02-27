from flask import Blueprint, render_template
# from flask import current_app as app
main = Blueprint('main', __name__)

from app.ZillowAPI.ZillowAddress import ZillowAddress
from app.ZillowAPI.ZillowAPICall import *
from app.DataBaseFunc import dbmethods
from joblib import load
import json
import pandas as pd
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
model = load('linear_regression_model.joblib')
def NewListing(location, daysonzillow,bedrooms=5,bathrooms=5, living_space=2000):

    newlistings = SearchZillowNewListingByLocation(location,daysonzillow)
    dbmethods.SaveHouseSearchDataintoDB(newlistings)
    listings = dbmethods.ActiveListings(daysupperlimit=daysonzillow,homeType="SINGLE_FAMILY")
    addresses=[]
    newbuildestimate_pred=[]
    for listing in listings:

        Addr = dbmethods.getBellevueTaxAddressbyAddress(listing)# returns 1 bellevuetax instance
        if Addr:
            addressStr = Addr.addr_full + '  ' + Addr.postalcityname + ' ' + str(Addr.zip5)

            zaddress = ZillowAddress.OpenAddresstxt(addressStr)
            addresses.append(zaddress)

            df = pd.DataFrame([Addr.__dict__])
            df = df.drop('_sa_instance_state', axis=1)
            df['bedrooms'][0] = float(bedrooms)
            df['bathrooms'][0] = float(bathrooms)
            df['living_area'][0] = int(living_space)
            newbuildestimate_pred.append(model.predict(df)[0])

        else:
            propertydata = SearchZillowByAddress(listing.streetAddress + '  ' + listing.city )
            bAddr = dbmethods.addToBellevueTaxAddress(propertydata)
            print(bAddr)
            df = pd.DataFrame([bAddr.__dict__])
            df = df.drop('_sa_instance_state', axis=1)
            # df['bedrooms'][0] = float(bedrooms)
            # df['bathrooms'][0] = float(bathrooms)
            # df['living_area'][0] = int(living_space)
            newbuildestimate_pred.append(model.predict(df)[0])
            addressStr = propertydata['address']['streetAddress'] + '  ' + propertydata['address']['city'] + ' ' + propertydata['address']['zipcode']
            json_string = json.dumps(propertydata, indent=4)
            with open(os.path.join('addressjson', addressStr + '.txt'), 'w') as f:
                f.write(json_string)
            zaddress = ZillowAddress.OpenAddresstxt(addressStr)
            addresses.append(zaddress)

    id = 0
    infodump=[]
    for ind,address in enumerate(addresses):
        images = []
        for photo in address.photos:
            for jpeg in photo['mixedSources']['jpeg']:
                if jpeg['width']==384:
                    images.append({
                        "url": jpeg['url'], "caption": photo['caption']
                    })
        equitygain =  newbuildestimate_pred[ind] - 1500000- address.price
        makemoney = True if equitygain>0 else False
        infodump.append(
            (address,f"carid{str(id)}",
             images, "{:,}".format(round(newbuildestimate_pred[ind])) ,
             "{:,}".format(round(address.price)),
             "{:,}".format(round(equitygain)),
             makemoney
             ))
        id = id +1
    # session['infodump'] = infodump  # Set session data

    return listings,infodump


def NewListingForEmail(location, daysonzillow,bedrooms=None,bathrooms=None, living_space=None):
    houseresult = SearchZillowNewListingByLocation(location,daysonzillow)
    infodump = []
    for house in houseresult:
        images=[]
        count = 0
        listingdetails = SearchZillowByZPID(house['zpid'])
        if not listingdetails:
            continue
        try:
            if listingdetails['address']['city']!='Seattle':
                continue
            print(listingdetails['address']['streetAddress'], listingdetails['address']['city'])
            neighbourhood = get_neighborhood(listingdetails['latitude'], listingdetails['longitude'])
            if not (neighbourhood in Config.NEIGHBORHOODS):
                print(neighbourhood)
                continue
            for photo in listingdetails['photos']:
                for jpeg in photo['mixedSources']['jpeg']:
                    if jpeg['width']==384:
                        images.append({
                            "url": jpeg['url'], "caption": photo['caption']
                        })
                        count = count +1
                if count>4:
                    break

            infodump.append(
                (listingdetails,f"{house['zpid']}",images,neighbourhood)
            )
        except Exception as e:
            print(e)


    return render_template('Email_House_List.html', infodump=infodump)

