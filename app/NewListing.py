from flask import Blueprint,render_template
main = Blueprint('main', __name__)
import json
import os
from LoadAddress import ZillowAddress
from app.ZillowSearch import UpdateListfromLocation, SearchNewListing,SearchNewSoldHomes,SearchProperty
from app.DataBaseFunc import dbmethods
from joblib import load
model = load('linear_regression_model.joblib')
import pandas as pd
def NewListing(request):
    # addresses = ["Address 1", "Address 2", "Address 3"]
    SearchNewListing('Bellevue')
    listings = dbmethods.ActiveListings(daysupperlimit=14,homeType="SINGLE_FAMILY")
    addresses=[]
    newbuildestimate_pred=[]
    for listing in listings:

        bellevueAddr = dbmethods.getBellevueTaxAddressbyAddress(listing)# returns 1 bellevuetax instance
        if bellevueAddr:
            addressStr = bellevueAddr.addr_full + '  ' + bellevueAddr.postalcityname + ' ' + str(bellevueAddr.zip5)
            propertydata = SearchProperty(addressStr)
            json_string = json.dumps(propertydata, indent=4)
            with open(os.path.join('addressjson', addressStr + '.txt'), 'w') as f:
                f.write(json_string)
            zaddress = ZillowAddress.OpenAddresstxt(addressStr)
            addresses.append(zaddress)

            df = pd.DataFrame([bellevueAddr.__dict__])
            df = df.drop('_sa_instance_state', axis=1)
            newbuildestimate_pred.append(model.predict(df)[0])

        else:
            propertydata = SearchProperty(listing.streetAddress + '  ' + listing.city )
            bAddr = dbmethods.addToBellevueTaxAddress(propertydata)
            print(bAddr)
            df = pd.DataFrame([bAddr.__dict__])
            df = df.drop('_sa_instance_state', axis=1)
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
        infodump.append((address,f"carid{str(id)}", images, round(newbuildestimate_pred[ind])))
        id = id +1

    return listings,infodump