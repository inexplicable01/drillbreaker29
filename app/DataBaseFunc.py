# from datetime import datetime
# # from app.DBModels.Listing import Listing
# from app.DBModels.BellevueTaxAddress import BellevueTaxAddress
# from sqlalchemy.sql import func, or_
# # from app.useful_func import haversine
# from haversine import haversine, Unit
# import pandas as pd
# import re
# from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
#
#
# class DBMETHOD():
#     #Should only be getters and setters
#
#
#     def __init__(self, db=None, Listing=Listing):
#         self.db = db
#         self.Listing = Listing
#
#     def AllListigs(self):
#         return self.Listing.query.all()
#
#     def AllBellevueAddress(self):
#         return BellevueTaxAddress.query.limit(100).all()
#
#     def AllListingsByDate(self):
#         return self.Listing.query.order_by(self.Listing.soldtime).all()
#
#     def ActiveListings(self, daysupperlimit=14, homeTypes=["SINGLE_FAMILY"]):
#         return self.Listing.query.filter(
#             self.Listing.daysOnZillow.between(0, daysupperlimit),
#             or_(*[self.Listing.homeType == homeType for homeType in homeTypes])
#         ).order_by(self.Listing.daysOnZillow).all()
#
#     def AllListingsforHeatmap(self):
#         results = self.Listing.query.all()
#         verifiedresults = []
#         for index, result in enumerate(results):
#             if result is None:
#                 # print(f"None found at index {index}")
#                 continue
#             else:
#                 # Assuming 'Listing' has an 'id' attribute
#                 # print(f"Listing ID: {result.id}")
#                 verifiedresults.append(result)
#
#         return results
#
#     def AddressesBuiltWithinLast4years(self):
#         current_year = datetime.now().year
#         threshold_year = current_year - 4
#         results = BellevueTaxAddress.query.filter(BellevueTaxAddress.year_built >= threshold_year).all()
#         verifiedresults = []
#         for index, result in enumerate(results):
#             if result is None:
#                 # print(f"None found at index {index}")
#                 continue
#             else:
#                 # Assuming 'Listing' has an 'id' attribute
#                 # print(f"Listing ID: {result.id}")
#                 verifiedresults.append(result)
#         return verifiedresults
#
#     def AddressesBuiltYearsAgo(self, Years=10):
#         current_year = datetime.now().year
#         threshold_year = current_year - Years
#         results = BellevueTaxAddress.query.filter(BellevueTaxAddress.year_built <= threshold_year).all()
#         verifiedresults = []
#         for index, result in enumerate(results):
#             if result is None:
#                 # print(f"None found at index {index}")
#                 continue
#             else:
#                 # Assuming 'Listing' has an 'id' attribute
#                 # print(f"Listing ID: {result.id}")
#                 if result.postalcityname == 'BELLEVUE':
#                     verifiedresults.append(result)
#         return verifiedresults
#
#     # def loadHouseSearchDataintoDB(self, housearray, status='solded'):
#     #     for house in housearray:
#     #         # Check if a listing with this zpid already exists.
#     #         # filtered_house = {k: house[k] for k in keystokeep if k in house}
#     #         listing = self.Listing.query.filter_by(zpid=house['zpid']).first()
#     #         if listing is None:
#     #              new_listing = Listing.CreateListing(house,status)
#     #              self.db.session.add(new_listing)
#     #         else:
#     #             for key, value in house.items():
#     #                 setattr(listing, key, value)
#     #         try:
#     #             self.db.session.commit()
#     #         except Exception as e:
#     #             # Handle the error, e.g., log it or notify the user.
#     #             self.db.session.rollback()
#     #             print(f"Error during insertion: {e}")
#
#     def find_addresses_within_distance(self, origin_lat, origin_long, distance_miles):
#         distance_query = BellevueTaxAddress.query.filter(
#             func.sqrt(
#                 func.pow(BellevueTaxAddress.latitude - origin_lat, 2) +
#                 func.pow(BellevueTaxAddress.longitude - origin_long, 2)
#             ) * 0.621371 <= distance_miles
#         )
#         # Since the above calculation is in kilometers, it's converted to miles by multiplying with 0.621371
#         # Now, to get the actual addresses, iterate through the results
#         addresses_with_distances = []
#         for address in distance_query:
#             # Calculate the distance using the haversine function
#             distance = haversine((origin_lat, origin_long), (address.latitude, address.longitude), unit=Unit.MILES)
#             if distance <= distance_miles:
#                 addresses_with_distances.append({
#                     'address': address,
#                     'distance': distance
#                 })
#
#         # Sort the list by distance
#         addresses_with_distances.sort(key=lambda x: x['distance'])
#
#         return addresses_with_distances
#
#     def find_Average_New_Build_Prices(self, address: BellevueTaxAddress, searchradius=1):
#         addresses_with_distances = self.find_addresses_within_distance(address.latitude, address.longitude,
#                                                                        searchradius)
#         averageprice = []
#         averagepriceitems = []
#         for item in addresses_with_distances:
#             closeaddress = item['address']
#             try:
#                 if len(averageprice) > 10:
#                     break
#                 if closeaddress.year_built > 2018:
#                     # print(closeaddress.detailStr())
#                     averageprice.append(closeaddress.zestimate_value)
#                     averagepriceitems.append(item)
#             except Exception as e:
#                 continue
#         if len(averageprice) == 0:
#             averagenewbuildprice = address.zestimate_value
#         else:
#             averagenewbuildprice = sum(averageprice) / len(averageprice)
#         return averagenewbuildprice, averagepriceitems
#
#     def find_addresses_based_on_Addr_full(self, addr_full):
#         return BellevueTaxAddress.query.filter_by(addr_full=addr_full).first()
#
#     # find_Average_New_Build_Prices(self, address: BellevueTaxAddress):return averagenewbuildprice, averagepriceaddress
#     def SaveHouseSearchDataintoDB(self, housearray, status='solded'):
#         for house in housearray:
#             # Check if a listing with this zpid already exists.
#             # filtered_house = {k: house[k] for k in keystokeep if k in house}
#             # 'zpid', 'price', 'unit', 'streetAddress',
#             # 'city', 'state', 'zipcode', 'bedrooms',
#             # 'bathrooms', 'zestimate', 'daysOnZillow',
#             # 'dateSold', 'homeType', 'latitude', 'longitude'
#             if 'dateSold' not in house.keys():
#                 house['dateSold'] = 0
#             try:
#                 filtered_house = {
#                     'zpid': house['zpid'],
#                     'price': safe_float_conversion(house['price']),
#                     'unit': 'house',
#                     'streetAddress': house['streetAddress'],
#                     'city': house['city'],
#                     'state': house['state'],
#                     'zipcode': safe_int_conversion(house['zipcode']),
#                     'bedrooms': safe_int_conversion(house['bedrooms']),
#                     'bathrooms': safe_float_conversion(house['bathrooms']),
#                     'zestimate': safe_float_conversion(house['zestimate']),
#                     'daysOnZillow': safe_int_conversion(house['daysOnZillow']),
#                     'latitude': safe_float_conversion(house['latitude']),
#                     'longitude': safe_float_conversion(house['longitude']),
#                     'homeType': house['homeType'],
#                     'dateSold': datetime.utcfromtimestamp(int(house['dateSold']) / 1000),
#                     'status': status
#                     # ... other fields ...
#                 }
#             except Exception as e:
#                 continue
#
#             listing = self.Listing.query.filter_by(zpid=filtered_house['zpid']).first()
#
#             try:
#                 if not listing:
#                     # Convert dictionary to a Listing object and add it to the session.
#                     new_listing = self.Listing(**filtered_house)
#                     print(new_listing)
#                     self.db.session.add(new_listing)
#                 else:
#                     # Update the existing listing with new data.
#                     for key, value in filtered_house.items():
#                         setattr(listing, key, value)
#                 # db.session.add(new_listing)
#                 self.db.session.commit()
#             except Exception as e:
#                 # Handle the error, e.g., log it or notify the user.
#                 self.db.session.rollback()
#                 print(f"Error during insertion: {e}")
#
#     def UpdateDB(self, entries_to_update):
#         try:
#             print_and_log('updating')
#             self.db.session.bulk_update_mappings(BellevueTaxAddress, entries_to_update)
#             print_and_log('commiting')
#             self.db.session.commit()
#         except Exception as e:
#             print_and_log(f"Error during bulk update: {str(e)}")
#             self.db.session.rollback()
#
#     def WaterFrontProps(self):
#
#         results = BellevueTaxAddress.query.filter(BellevueTaxAddress.haswaterfrontview == True).all()
#         verifiedresults = []
#         for index, result in enumerate(results):
#             if result is None:
#                 continue
#             else:
#                 verifiedresults.append(result)
#         return verifiedresults
#
#     def PropertiesBuiltAfter(self, year: int = 2016):
#         results = BellevueTaxAddress.query.filter(BellevueTaxAddress.year_built > year)
#         result_set = results.all()
#         df = pd.DataFrame([row.__dict__ for row in result_set])
#         df = df.drop('_sa_instance_state', axis=1)
#         return df
#
#     def returnBellevueTaxAddress(self, addr_full):
#         results = BellevueTaxAddress.query.filter(BellevueTaxAddress.addr_full==addr_full)
#         result_set = results.all()
#         df = pd.DataFrame([row.__dict__ for row in result_set])
#         df = df.drop('_sa_instance_state', axis=1)
#         return df
#
#     def addToBellevueTaxAddress(self,propertdata):
#         return BellevueTaxAddress.create_from_dict(propertdata)
#
# #this function looks for the Bellevue Tax Address where is the most comprehenisve schema in your DB.
#     ##
#     def getBellevueTaxAddressbyAddress(self,listing):
#         pattern = r"^(\d+)\s+(.*?)(?:\s+SE|\s+NE|\s+RD|\s+AVE|\s+ST|)?$"
#         streetaddress = listing.streetAddress
#
#         match = re.match(pattern, streetaddress)
#         if match:
#             house_number, street_name = match.groups()
#             street_name = street_name.lower()
#             if "avenue" in street_name:
#                 street_name = street_name.replace("avenue","ave")
#             if "street" in street_name:
#                 street_name = street_name.replace("street","st")
#             if "key" in street_name:
#                 street_name = street_name.replace("key","ky")
#             query =  BellevueTaxAddress.query.filter(
#                 BellevueTaxAddress.addr_full.like(f'%{house_number}%'),
#                 BellevueTaxAddress.addr_full.like(f'%{street_name}%')).all()
#             if len(query)==0:
#                 print(f'Unable to find match for {streetaddress}')
#                 return None
#             if len(query)>2:
#                 min_distance = float('inf')  # Initialize with a very large number
#                 closest_belladdr = None
#                 for belladdr in query:
#                     distance = (listing.longitude - belladdr.longitude)**2 + (listing.latitude - belladdr.latitude)**2
#                     if distance < min_distance:
#                         min_distance = distance
#                         closest_belladdr = belladdr
#                 print(f'Too many matches for {streetaddress}')
#                 return closest_belladdr
#             return query[0]
#         print(f'RegGex Failed  for {streetaddress}')
#         return None
#
# dbmethods = DBMETHOD()
