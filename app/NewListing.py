from flask import Blueprint,session, render_template
# from flask import current_app as app
main = Blueprint('main', __name__)

import json
import os
from LoadAddress import ZillowAddress
from app.ZillowSearch import *
from app.DataBaseFunc import dbmethods
from joblib import load
model = load('linear_regression_model.joblib')
import pandas as pd
api_key = os.getenv('GOOGLE_API_KEY')
NEIGHBORHOODS = ['Ballard', 'Fremont', 'Crown Hill', 'Green Wood', 'Phinney Ridge', 'Wallingford', 'North Beach',
                 'Blue Ridge', 'Whittier Heights', 'Loyal Heights', 'Sunset Hill', 'Magnolia', 'Queen Anne']
def NewListing(location, daysonzillow,bedrooms=5,bathrooms=5, living_space=2000):

    SearchNewListing(location,daysonzillow)

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
            propertydata = SearchProperty(listing.streetAddress + '  ' + listing.city )
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
def get_neighborhood(lat, lon):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    for component in data['results'][0]['address_components']:
        if 'neighborhood' in component['types']:
            return component['long_name']
    return None
def NewListingInNeighbourhoods(location, daysonzillow,bedrooms=5,bathrooms=5, living_space=2000):

    SearchNewListing(location,daysonzillow)

    listings = dbmethods.ActiveListings(daysupperlimit=daysonzillow,
                                        homeTypes=["SINGLE_FAMILY","TOWNHOUSE","CONDO"])
    addresses=[]
    newbuildestimate_pred=[]
    for listing in listings:
        try:
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
                propertydata = SearchProperty(listing.streetAddress + '  ' + listing.city )
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
        except:
            print(listing.streetAddress + '  ' + listing.city ,' error')

    id = 0
    infodump=[]
    for ind,address in enumerate(addresses):
        images = []
        if address.address['city']!='Seattle':
            continue
        print(address.address['streetAddress'], address.address['city'])
        neighbourhood = get_neighborhood(address.latitude, address.longitude)
        print()
        if not (neighbourhood in NEIGHBORHOODS):
            continue
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
             makemoney,
             neighbourhood
             ))
        id = id +1
    # session['infodump'] = infodump  # Set session data

    return listings,infodump

def NewListingForEmail(location, daysonzillow,bedrooms=None,bathrooms=None, living_space=None):

    houseresult = SearchNewListing(location,daysonzillow)
    infodump = []
    for house in houseresult:
        images=[]
        count = 0
        listingdetails = SearchListingByZPID(house['zpid'])

        if listingdetails['address']['city']!='Seattle':
            continue
        print(listingdetails['address']['streetAddress'], listingdetails['address']['city'])
        neighbourhood = get_neighborhood(listingdetails['latitude'], listingdetails['longitude'])
        if not (neighbourhood in NEIGHBORHOODS):
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


    return render_template('Email_House_List.html', infodump=infodump)