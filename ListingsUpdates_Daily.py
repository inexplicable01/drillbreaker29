import requests
import os

url = f"https://www.drillbreaker29.com/maintanance/maintainListings" ## this is a good daily check that sees if 1 there are new listings, 2 pending listings, 3 sold listings

# url2 = f"https://www.drillbreaker29.com/maintanance/updatelistings"
# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"



##Need FSBO weekly Update
##Need All ForSale Listing Weekly Update

payload = {}
headers = {}

# response = requests.request("PATCH", url2, headers=headers, data={'doz': '1095'})
response = requests.request("PATCH", url, headers=headers, data=payload)
# response = requests.request("PATCH", url3, headers=headers, data=payload)
print(response.text)
