import requests
from datetime import datetime
import sys
base = "http://127.0.0.1:5000/"
# base = "https://www.drillbreaker29.com/"

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


message = ''
for customer in activeCustomers:
    print(customer)

url = f"{base}email/sendEmailOutToLeads"
response = requests.request("POST", url, headers=headers, data=payload)






