import requests
from datetime import datetime
import sys
import json
import os
# base = os.getenv("BASE")
# base = "http://127.0.0.1:5000/"
base = "https://www.drillbreaker29.com/"

getcitylisturl = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"
getsoldlistingsurl = base + "maintanance/maintainSoldListings"
getforsalelistingsurl = base + "maintanance/maintainFORSALEListings"
getpendinglistingsurl = base + "maintanance/maintainPendingListings"
# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"{base}maintanance/fsbo"
urlopen = f"{base}maintanance/updateopenhouse"

params = []
payload = {}
headers = {}



url = f"{base}listingalerts/activeCustomers"

payload = {}
headers = {}
# print(url)
response = requests.request("GET", url, headers=headers, data=payload)

activeCustomers = response.json()['activeCustomers']
level1_2seller = response.json()['level1_2seller']
level1_2buyer = response.json()['level1_2buyer']
level3_buyer = response.json()['level3_buyer']


message = ''
test = True

# for customer in level1_2seller:
#     url = f"{base}email/sendEmailOutToLeads"
#     payload = {**customer, "test":test, "group":"3"}  # or "true"
#     headers = {
#         # DON'T set application/json here
#         "Content-Type": "application/x-www-form-urlencoded",
#         # include your auth headers, if any
#     }
#     response = requests.request("POST", url, headers=headers, data=payload)
#     break

payload = json.dumps({
  "forreal": False,
  "test": test
})
headers = {
  'Content-Type': 'application/json'
}
url = f"{base}campaign/sendLevel1Buyer_sendEmail"
response = requests.request("GET", url, headers=headers, data=payload)



# for customer in level1_2buyer:
#     url = f"{base}email/sendEmailOutToLeads"
#     payload = {**customer, "test": test, "group":"1"}  # or "true"
#     headers = {
#         # DON'T set application/json here
#         "Content-Type": "application/x-www-form-urlencoded",
#         # include your auth headers, if any
#     }
#     response = requests.request("POST", url, headers=headers, data=payload)
#     break
#
# for customer in level3_buyer:
#     url = f"{base}email/sendEmailOutToLeads"
#     payload = {**customer, "test": test, "group":"2"}  # or "true"
#     headers = {
#         # DON'T set application/json here
#         "Content-Type": "application/x-www-form-urlencoded",
#         # include your auth headers, if any
#     }
#     response = requests.request("POST", url, headers=headers, data=payload)
#     break








