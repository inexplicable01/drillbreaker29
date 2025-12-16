# from app.ZillowAPI.ZillowDataProcessor import SearchZillowNewListingByLocation,SearchZillowByAddress
# from app.DataBaseFunc import dbmethods
# from app.ZillowAPI.ZillowAddress import ZillowAddress
# import pandas as pd
# from app.UsefulAPI.UseFulAPICalls import get_neighborhood
# from app.config import Config
# from joblib import load
# import os
# import json
# model = load('linear_regression_model.joblib')
#
# def NewListingInNeighbourhoods(location, daysonzillow,bedrooms=5,bathrooms=5, living_space=2000):
#
#     newlistings = SearchZillowNewListingByLocation(location,daysonzillow)
#     dbmethods.SaveHouseSearchDataintoDB(newlistings)
#     listings = dbmethods.ActiveListings(daysupperlimit=daysonzillow,
#                                         homeTypes=["SINGLE_FAMILY","TOWNHOUSE","CONDO"])
#     addresses=[]
#     newbuildestimate_pred=[]
#     for listing in listings:
#         try:
#             Addr = dbmethods.getBellevueTaxAddressbyAddress(listing)# returns 1 bellevuetax instance
#             if Addr:
#                 addressStr = Addr.addr_full + '  ' + Addr.postalcityname + ' ' + str(Addr.zip5)
#
#                 zaddress = ZillowAddress.OpenAddresstxt(addressStr)
#                 addresses.append(zaddress)
#
#                 df = pd.DataFrame([Addr.__dict__])
#                 df = df.drop('_sa_instance_state', axis=1)
#                 df['bedrooms'][0] = float(bedrooms)
#                 df['bathrooms'][0] = float(bathrooms)
#                 df['living_area'][0] = int(living_space)
#                 newbuildestimate_pred.append(model.predict(df)[0])
#
#             else:
#                 propertydata = SearchZillowByAddress(listing.streetAddress + '  ' + listing.city )
#                 bAddr = dbmethods.addToBellevueTaxAddress(propertydata)
#                 print(bAddr)
#                 df = pd.DataFrame([bAddr.__dict__])
#                 df = df.drop('_sa_instance_state', axis=1)
#                 # df['bedrooms'][0] = float(bedrooms)
#                 # df['bathrooms'][0] = float(bathrooms)
#                 # df['living_area'][0] = int(living_space)
#                 newbuildestimate_pred.append(model.predict(df)[0])
#                 addressStr = propertydata['address']['streetAddress'] + '  ' + propertydata['address']['city'] + ' ' + propertydata['address']['zipcode']
#                 json_string = json.dumps(propertydata, indent=4)
#                 with open(os.path.join('addressjson', addressStr + '.txt'), 'w') as f:
#                     f.write(json_string)
#                 zaddress = ZillowAddress.OpenAddresstxt(addressStr)
#                 addresses.append(zaddress)
#         except:
#             print(listing.streetAddress + '  ' + listing.city ,' error')
#
#     id = 0
#     infodump=[]
#     for ind,address in enumerate(addresses):
#         images = []
#         if address.address['city']!='Seattle':
#             continue
#         print(address.address['streetAddress'], address.address['city'])
#         neighbourhood = get_neighborhood(address.latitude, address.longitude)
#         print()
#         if not (neighbourhood in Config.NEIGHBORHOODS):
#             continue
#         for photo in address.photos:
#             for jpeg in photo['mixedSources']['jpeg']:
#                 if jpeg['width']==384:
#                     images.append({
#                         "url": jpeg['url'], "caption": photo['caption']
#                     })
#         equitygain =  newbuildestimate_pred[ind] - 1500000- address.price
#         makemoney = True if equitygain>0 else False
#         infodump.append(
#             (address,f"carid{str(id)}",
#              images, "{:,}".format(round(newbuildestimate_pred[ind])) ,
#              "{:,}".format(round(address.price)),
#              "{:,}".format(round(equitygain)),
#              makemoney,
#              neighbourhood
#              ))
#         id = id +1
#     # session['infodump'] = infodump  # Set session data
#
#     return listings,infodump
