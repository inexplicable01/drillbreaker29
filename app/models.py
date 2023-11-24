# from datetime import datetime
# from app import db
# from app.useful_func import safe_float_conversion,safe_int_conversion
# # Define your database model outside of create_app so it's globally available
#
#
#
#
# def AllListings():
#     results = Listing.query.all()
#     verifiedresults=[]
#     for index, result in enumerate(results):
#         if result is None:
#             # print(f"None found at index {index}")
#             continue
#         else:
#             # Assuming 'Listing' has an 'id' attribute
#             # print(f"Listing ID: {result.id}")
#             verifiedresults.append(result)
#
#     return results
#
# def SaveHouseSearchDataintoDB(housearray, status='solded'):
#     for house in housearray:
#         # Check if a listing with this zpid already exists.
#         # filtered_house = {k: house[k] for k in keystokeep if k in house}
#         # 'zpid', 'price', 'unit', 'streetAddress',
#         # 'city', 'state', 'zipcode', 'bedrooms',
#         # 'bathrooms', 'zestimate', 'daysOnZillow',
#         # 'dateSold', 'homeType', 'latitude', 'longitude'
#         if 'dateSold' not in house.keys():
#             house['dateSold'] =0
#         try:
#             filtered_house = {
#                 'zpid': house['zpid'],
#                 'price': safe_float_conversion(house['price']),
#                 'unit': 'house',
#                 'streetAddress': house['streetAddress'],
#                 'city': house['city'],
#                 'state': house['state'],
#                 'zipcode': safe_int_conversion(house['zipcode']),
#                 'bedrooms': safe_int_conversion(house['bedrooms']),
#                 'bathrooms': safe_float_conversion(house['bathrooms']),
#                 'zestimate': safe_float_conversion(house['zestimate']),
#                 'daysOnZillow': safe_int_conversion(house['daysOnZillow']),
#                 'latitude': safe_float_conversion(house['latitude']),
#                 'longitude': safe_float_conversion(house['longitude']),
#                 'homeType': house['homeType'],
#                 'dateSold': datetime.utcfromtimestamp(int(house['dateSold']) / 1000),
#                 'status':status
#                 # ... other fields ...
#             }
#         except Exception as e:
#             continue
#
#
#         listing = Listing.query.filter_by(zpid=filtered_house['zpid']).first()
#
#         try:
#             if not listing:
#                 # Convert dictionary to a Listing object and add it to the session.
#                 new_listing = Listing(**filtered_house)
#                 print(new_listing)
#                 db.session.add(new_listing)
#             else:
#                 # Update the existing listing with new data.
#                 for key, value in filtered_house.items():
#                     setattr(listing, key, value)
#             # db.session.add(new_listing)
#             db.session.commit()
#         except Exception as e:
#             # Handle the error, e.g., log it or notify the user.
#             print(f"Error during insertion: {e}")