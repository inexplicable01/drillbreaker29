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


getcitylisturl = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"
getsoldlistingsurl = base + "maintanance/maintainSoldListings"
getforsalelistingsurl = base + "maintanance/maintainFORSALEListings"
getpendinglistingsurl = base + "maintanance/maintainPendingListings"
# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"{base}maintanance/fsbo"
urlopen = f"{base}maintanance/updateopenhouse"

params = [("county", "King"), ("county", "Snohomish"), ("county", "Skagit")]
payload = {}
headers = {}

# Exit early if not Monday or Thursday
# if datetime.today().weekday() not in [0, 3]:
#     print("Not Monday or Thursday. Exiting script.")
#     sys.exit()

response = requests.request("GET", getcitylisturl,  params=params, headers=headers, data=payload)

# Collect all stats from updates
all_stats = {
    'cities_processed': [],
    'total_sold_updates': 0,
    'total_pending_updates': 0,
    'total_forsale_updates': 0,
    'sold_details': [],
    'pending_details': [],
    'forsale_details': []
}

for i, city in enumerate(response.json()["cities"]):
    # if city != "Seattle":
    #     continue
    print(f"\n{'='*60}")
    print(f"Processing {city}")
    print(f"{'='*60}")

    all_stats['cities_processed'].append(city)
    files = []
    headers = {}

    # Update Sold Listings
    payload = {'doz': '90', 'city': city}
    sold_res = requests.request("PATCH", getsoldlistingsurl, headers=headers, data=payload, files=files)
    print(f"Sold response: {sold_res.status_code}")

    if sold_res.status_code == 200:
        sold_data = sold_res.json()
        if 'stats' in sold_data:
            all_stats['sold_details'].append(sold_data['stats'])
            all_stats['total_sold_updates'] += sold_data['stats'].get('new_sold', 0)

    # Update For Sale Listings
    payload = {'doz': '180', 'city': city}
    forsale_res = requests.request("PATCH", getforsalelistingsurl, headers=headers, data=payload, files=files)
    print(f"For Sale response: {forsale_res.status_code}")

    if forsale_res.status_code == 200:
        forsale_data = forsale_res.json()
        if 'stats' in forsale_data:
            all_stats['forsale_details'].append(forsale_data['stats'])
            all_stats['total_forsale_updates'] += forsale_data['stats'].get('new_for_sale', 0)

    # Update Pending Listings
    payload = {'doz': '60', 'city': city}
    pending_res = requests.request("PATCH", getpendinglistingsurl, headers=headers, data=payload, files=files)
    print(f"Pending response: {pending_res.status_code}")

    if pending_res.status_code == 200:
        pending_data = pending_res.json()
        if 'stats' in pending_data:
            all_stats['pending_details'].append(pending_data['stats'])
            all_stats['total_pending_updates'] += pending_data['stats'].get('pending_to_sold', 0) + pending_data['stats'].get('pending_to_forsale', 0)

# Update zone stats
payload = {}
response = requests.request("POST", base+"zonestats/update", headers=headers, data=payload)

# Build comprehensive email message
email_message = "3 County Update Summary\n"
email_message += "=" * 60 + "\n\n"

for city_stats in all_stats['sold_details']:
    email_message += f"\n{city_stats['city']} - SOLD LISTINGS:\n"
    email_message += f"  Total API Results: {city_stats['total_api_results']}\n"
    email_message += f"  New Sold: {city_stats['new_sold']}\n"
    email_message += f"  Pending → Sold: {city_stats['pending_to_sold']}\n"
    email_message += f"  For Sale → Sold: {city_stats['forsale_to_sold']}\n"
    email_message += f"  Customer Alerts: {city_stats['customer_alerts_sent']}\n"

    if city_stats['pending_to_sold_list']:
        email_message += f"\n  Properties that went Pending → Sold:\n"
        for prop in city_stats['pending_to_sold_list'][:10]:  # Limit to first 10
            email_message += f"    - {prop['address']} (${prop['price']:,})\n"

    if city_stats['forsale_to_sold_list']:
        email_message += f"\n  Properties that went For Sale → Sold:\n"
        for prop in city_stats['forsale_to_sold_list'][:10]:  # Limit to first 10
            email_message += f"    - {prop['address']} (${prop['price']:,})\n"

for city_stats in all_stats['pending_details']:
    email_message += f"\n{city_stats['city']} - PENDING LISTINGS:\n"
    email_message += f"  Total Checked: {city_stats['total_pending_checked']}\n"
    email_message += f"  Still Pending: {city_stats['still_pending']}\n"
    email_message += f"  Pending → For Sale: {city_stats['pending_to_forsale']}\n"
    email_message += f"  Pending → Sold: {city_stats['pending_to_sold']}\n"

    if city_stats['pending_to_forsale_list']:
        email_message += f"\n  Properties that went back For Sale:\n"
        for prop in city_stats['pending_to_forsale_list'][:10]:
            email_message += f"    - {prop['address']} (${prop['price']:,})\n"

for city_stats in all_stats['forsale_details']:
    email_message += f"\n{city_stats['city']} - FOR SALE LISTINGS:\n"
    email_message += f"  Total API Results: {city_stats['total_api_results']}\n"
    email_message += f"  New Listings: {city_stats['new_for_sale']}\n"
    email_message += f"  Price Changes: {city_stats['price_changes']}\n"
    email_message += f"  Mismanaged: {city_stats['mismanaged']}\n"

    if city_stats['new_for_sale_list']:
        email_message += f"\n  New listings that came online:\n"
        for prop in city_stats['new_for_sale_list'][:10]:
            email_message += f"    - {prop['address']} (${prop['price']:,})\n"

    if city_stats['price_changes_list']:
        email_message += f"\n  Price changes:\n"
        for prop in city_stats['price_changes_list'][:10]:
            email_message += f"    - {prop['address']}: ${prop['old_price']:,} → ${prop['new_price']:,}\n"

email_message += f"\n\n{'='*60}\n"
email_message += f"TOTALS:\n"
email_message += f"  Cities Processed: {', '.join(all_stats['cities_processed'])}\n"
email_message += f"  Total New Sold: {all_stats['total_sold_updates']}\n"
email_message += f"  Total For Sale: {all_stats['total_forsale_updates']}\n"
email_message += f"  Total Pending Changes: {all_stats['total_pending_updates']}\n"

url_health = f"{base}email/email_healthcheck"
payload = {'message': email_message}
response = requests.post(url_health, headers=headers, json=payload)
print(f"\nEmail sent: {response.status_code}")
print(email_message)

