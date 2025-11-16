import requests
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
import argparse
# # Load API key
# load_dotenv()
# base = os.getenv("BASE")

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

# Exit early if not Monday or Thursday
if datetime.today().weekday() not in [3]:
    print("Not Thursday. Exiting script.")
    sys.exit()

response = requests.request("GET", getcitylisturl,  params=params, headers=headers, data=payload)


for i,city in enumerate(response.json()["cities"]):
    # print(city)
    # if city!='Seattle':
    #     continue
    # if city not  in ["Lynnwood"]:
    #     continue
    print(city)
    payload = {'doz': '720',
               'city': city}
    files = []
    headers = {}

    # res = requests.request("PATCH", getsoldlistingsurl, headers=headers, data=payload, files=files)
    # print(res)
    payload = {'doz': '720',
               'city': city}
    res = requests.request("PATCH", getforsalelistingsurl, headers=headers, data=payload, files=files)
    print(res)
    payload = {'doz': '180',
               'city': city}
    res = requests.request("PATCH", getpendinglistingsurl, headers=headers, data=payload, files=files)
    # resp = requests.request("PATCH", url3, headers=headers, data=payload)
    print(res)

payload = {}
response = requests.request("POST", base+"zonestats/update", headers=headers, data=payload)



