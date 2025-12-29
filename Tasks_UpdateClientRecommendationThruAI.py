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
parser.add_argument(
    "--send-to-client",
    action="store_true",
    default=False,
    help="Send emails to clients instead of admin (default: False - sends to admin)",
)

args = parser.parse_args()

if args.base == "local":
    base = "http://127.0.0.1:5000/"
else:  # "prod"
    base = "https://www.drillbreaker29.com/"

# Display mode
print("="*50)
print(f"Running in {'PRODUCTION' if args.send_to_client else 'TESTING'} mode")
print(f"Emails will go to: {'CLIENTS' if args.send_to_client else 'ADMIN'}")
print("="*50)
print()

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

# Track totals across all customers
totals = {
    'customers_processed': 0,
    'customers_with_matches': 0,
    'total_evaluated': 0,
    'total_high_scoring': 0,
    'total_excellent': 0,
    'errors': 0,
    'customer_details': []
}

for customer in level3_buyer:
    try:
        # Add send_to_client parameter to URL
        send_to_client_param = "true" if args.send_to_client else "false"
        url = f"{base}maintanance/clients_listing_Recommendation?customer_id={customer['id']}&send_to_client={send_to_client_param}"
        response = requests.request("PATCH", url, headers=headers, data=payload)

        if response.status_code == 200:
            result = response.json()
            totals['customers_processed'] += 1
            totals['total_evaluated'] += result.get('Updated Recommendations', 0)
            totals['total_high_scoring'] += result.get('New High-Scoring Listings', 0)
            totals['total_excellent'] += result.get('Excellent Matches (90+)', 0)

            # Track customers who got matches
            if result.get('New High-Scoring Listings', 0) > 0:
                totals['customers_with_matches'] += 1
                totals['customer_details'].append({
                    'name': customer.get('name', 'Unknown'),
                    'id': customer['id'],
                    'high_scoring': result.get('New High-Scoring Listings', 0),
                    'excellent': result.get('Excellent Matches (90+)', 0)
                })

            print(f"✓ Processed {customer.get('name', 'Unknown')} (ID: {customer['id']}): {result.get('New High-Scoring Listings', 0)} matches")
        else:
            totals['errors'] += 1
            print(f"✗ Error processing {customer.get('name', 'Unknown')} (ID: {customer['id']}): HTTP {response.status_code}")

    except Exception as e:
        totals['errors'] += 1
        print(f"✗ Exception processing {customer.get('name', 'Unknown')} (ID: {customer['id']}): {e}")

# Send final summary email
print("\n" + "="*50)
print("FINAL SUMMARY")
print("="*50)
print(f"Customers Processed: {totals['customers_processed']}")
print(f"Customers with Matches: {totals['customers_with_matches']}")
print(f"Total Listings Evaluated: {totals['total_evaluated']}")
print(f"Total High-Scoring Listings: {totals['total_high_scoring']}")
print(f"Total Excellent Matches (90+): {totals['total_excellent']}")
print(f"Errors: {totals['errors']}")
print("="*50)

# Send summary email to admin
url_summary = f"{base}email/send_recommendation_summary"
summary_payload = {
    "totals": totals,
    "timestamp": datetime.now().isoformat()
}

try:
    response = requests.post(url_summary, headers=headers, json=summary_payload)
    print(f"\n✓ Summary email sent to admin")
except Exception as e:
    print(f"\n✗ Failed to send summary email: {e}")

url_health = f"{base}email/email_healthcheck"
payload = {"message": "completed customer AI listing"}

response = requests.post(url_health, headers=headers, json=payload)

