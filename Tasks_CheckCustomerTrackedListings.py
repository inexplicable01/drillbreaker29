"""
Check Customer-Tracked Listings for Changes

Daily task to check all listings that customers are tracking for changes
and send email alerts when price, status, or other important fields change.

Usage:
    python Tasks_CheckCustomerTrackedListings.py [--base local|prod]

For PythonAnywhere scheduled tasks:
    - Go to Tasks tab
    - Add new task with schedule (e.g., daily at 9:00 AM)
    - Command: python3 /path/to/Tasks_CheckCustomerTrackedListings.py --base prod
"""

import requests
from datetime import datetime
import argparse

parser = argparse.ArgumentParser(description='Check customer-tracked listings for changes')
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

print("=" * 70)
print("  CUSTOMER-TRACKED LISTINGS CHANGE CHECKER")
print("  Run time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("  Target:", base)
print("=" * 70)

# Check if current hour is divisible by 3 (runs at 0, 3, 6, 9, 12, 15, 18, 21)
current_hour = datetime.now().hour
if current_hour % 3 != 0:
    print(f"\n[SKIP] Current hour is {current_hour}, not divisible by 3.")
    print(f"[SKIP] Next run will be at hour {current_hour + (3 - current_hour % 3)}:00")
    print("\n" + "=" * 70)
    print("[SKIPPED]")
    print("=" * 70)
    exit(0)

print(f"\n[RUN] Current hour is {current_hour}, divisible by 3. Proceeding with check...")

# Make request to the endpoint
url = base + "maintanance/checkCustomerTrackedListings"

print(f"\n[REQUESTING] {url}")

try:
    response = requests.request("GET", url, headers={}, data={})

    if response.status_code == 200:
        result = response.json()

        print("\n[SUCCESS] Task completed")
        print(f"  Status: {result.get('status')}")
        print(f"  Message: {result.get('message')}")

        if 'stats' in result:
            stats = result['stats']
            print("\n[STATISTICS]")
            print(f"  Total tracked: {stats.get('total_tracked', 0)}")
            print(f"  Checked: {stats.get('checked', 0)}")
            print(f"  Changes detected: {stats.get('changes_detected', 0)}")
            print(f"  Alerts sent: {stats.get('alerts_sent', 0)}")
            print(f"  Errors: {stats.get('errors', 0)}")
    else:
        print(f"\n[ERROR] Request failed with status code: {response.status_code}")
        print(f"  Response: {response.text}")

except Exception as e:
    print(f"\n[ERROR] Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("[COMPLETE]")
print("=" * 70)
