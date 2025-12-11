import requests
from datetime import datetime
import sys
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--base",
    choices=["local", "prod"],
    default="local",
    help="Which base URL to use: 'local' or 'prod' (default: local)",
)

args = parser.parse_args()

if args.base == "local":
    base = "http://127.0.0.1:5000/"
else:  # "prod"
    base = "https://www.drillbreaker29.com/"

# from the project

getcitylisturl = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"
getsoldlistingsurl = base + "maintanance/maintainSoldListings"
getforsalelistingsurl = base + "maintanance/maintainFORSALEListings"
getpendinglistingsurl = base + "maintanance/maintainPendingListings"
# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"{base}maintanance/fsbo"
urlopen = f"{base}maintanance/updateopenhouse"

#

url = f"{base}listingalerts/activeCustomers"

payload = {}
headers = {}
# print(url)
response = requests.request("GET", url, headers=headers, data=payload)

level3_buyer = response.json()['level3_buyer']

for customer in level3_buyer:
    # print(customer)

    url = f"{base}maintanance/clients_listing_Recommendation?customer_id={customer['id']}"
    response = requests.request("PATCH", url, headers=headers, data=payload)

    # url = f"{base}customer_interest/send_email/{customer['id']}"
    # response = requests.request("POST", url, headers=headers, data=payload)

url_health = f"{base}email/email_healthcheck"
payload = {"message": "completed customer AI listing"}

response = requests.post(url_health, headers=headers, json=payload)

