import requests
from datetime import datetime
import sys
import json
import os
import argparse
# base = os.getenv("BASE")
from dotenv import load_dotenv
# Load API key
load_dotenv()
base = os.getenv("BASE")
# base = "http://127.0.0.1:5000/"
base = "https://www.drillbreaker29.com/"


def str2bool(v):
  if isinstance(v, bool):
    return v
  return v.strip().lower() in ("true", "1", "yes", "on")


parser = argparse.ArgumentParser()
parser.add_argument("--forreal", type=str2bool, nargs="?", const=True, default=False)
parser.add_argument("--ignoretimerestriction", type=str2bool, nargs="?", const=True, default=False)
parser.add_argument("--selectafew", type=str2bool, nargs="?", const=True, default=False)
parser.add_argument("--admin", type=str2bool, nargs="?", const=True, default=False)
args = parser.parse_args()



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

print(response.json())
activeCustomers = response.json()['activeCustomers']
level1_2seller = response.json()['level1_2seller']
level1_2buyer = response.json()['level1_2buyer']
level3_buyer = response.json()['level3_buyer']

message = ''

payload = {
    "forreal": args.forreal,   # <-- booleans, not strings
    "ignoretimerestriction":    args.ignoretimerestriction,
    "admin":   args.admin,
    "selectafew": args.selectafew
}

url = f"{base}campaign/sendLevel1Buyer_sendEmail"
response = requests.request("GET", url, headers=headers, json=payload)

url = f"{base}campaign/sendLevel1_2_Seller_sendEmail"
response = requests.request("GET", url, headers=headers, json=payload)
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








