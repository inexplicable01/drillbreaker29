import requests
import os
from warnings import warn
import time

import sqlite3
url = "https://zillow56.p.rapidapi.com/search"
# url ="https://zillow-com4.p.rapidapi.com/properties/search"
zpidurl = "https://zillow56.p.rapidapi.com/property"
keystokeep = ['zpid','price','unit','streetAddress',
              'city','state','zipcode','bedrooms',
              'bathrooms','zestimate','daysOnZillow',
              'dateSold','homeType','latitude','longitude']

headers = {
    "X-RapidAPI-Key": os.getenv('RAPID_API_KEY'),
    "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
}

# headers = {
# 	"x-rapidapi-key": os.getenv('RAPID_API_KEY'),
# 	"x-rapidapi-host": "zillow-com4.p.rapidapi.com"
# }

# from app.DataBaseFunc import dbmethods




def SearchZillowByZPID(ZPID):
    querystring = {"zpid": ZPID}
    response = requests.get("https://zillow56.p.rapidapi.com/property", headers=headers, params=querystring)
    time.sleep(0.5)
    try:
        return response.json()
    except Exception as e:
        warn(f"Search Zillow zpid {ZPID} failed due to an exception: {e}")
        return None

def SearchZilowByMLSID(MLSID):
    querystring = {"mls": MLSID}
    url = "https://zillow56.p.rapidapi.com/search_mls"
    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)
    try:
        data = response.json()

        # Iterate through response data to find the zpid for WA
        for property_data in data['data']:
            if "address" in property_data:
                # Extract and split the address to validate state
                address_parts = property_data["address"].split(",")  # Split address by commas

                if len(address_parts) >= 2:  # Ensure there's a city/state part and look at the last part
                    state_zip = address_parts[-1].strip()  # Get the last component of the address

                    # Validate state as "WA" (strict match)
                    if state_zip.startswith("WA "):  # Handle cases like "WA 98937"
                        return property_data["zpid"]
        warn(f"No property in WA found for MLSID {MLSID}.")
        return None

    except Exception as e:
        warn(f"Search Zillow zpid {MLSID} failed due to an exception: {e}")
        return None



def SearchZillowByAddress(addressStr):
    # querystring = {"location":location + ", wa","page": str(lastpage),"status":"forSale","doz":"14"}
    querystring = {"address": addressStr}
    response = requests.get("https://zillow56.p.rapidapi.com/search_address", headers=headers, params=querystring)
    time.sleep(0.5)
    if response.status_code==502:
        warn('502 on ' + addressStr)
    try:
        return response.json()
    except Exception as e:
        warn(f"Search Zillow failed due to an exception: {e}")
        return None

def SearchZillowBriefListingByAddress(addressStr):
     ##  this is when you have the full address and you still have to only get the brief version of the listing.
    querystring = {"location": addressStr,"output":"json","status":"forSale","doz":"any"}
    response = requests.get("https://zillow56.p.rapidapi.com/search", headers=headers, params=querystring)
    time.sleep(0.5)
    if response.status_code==502:
        warn('502 on ' + addressStr)
    try:
        return response.json()['results'][0]
    except Exception as e:
        warn(f"Search Zillow failed due to an exception: {e}")
        return None


def RentEstimateBriefListing(addressStr):
    ##  this is when you have the full address and you still have to only get the brief version of the listing.
    querystring = {"address":addressStr}
    response = requests.get("https://zillow56.p.rapidapi.com/rent_estimate", headers=headers, params=querystring)
    time.sleep(0.5)

    if response.status_code == 502:
        warn('502 on ' + addressStr)
    try:
        return response.json()
    except Exception as e:
        warn(f"Search Zillow failed due to an exception: {e}")
        return None



def SearchZillowBriefListingByAddress(addressStr):
    ##  this is when you have the full address and you still have to only get the brief version of the listing.
    querystring = {"location": addressStr, "output": "json", "status": "forSale", "doz": "any"}
    response = requests.get("https://zillow56.p.rapidapi.com/search", headers=headers, params=querystring)
    time.sleep(0.5)
    if response.status_code == 502:
        warn('502 on ' + addressStr)
    try:
        return response.json()['results'][0]
    except Exception as e:
        warn(f"Search Zillow failed due to an exception: {e}")
        return None


def SearchZillowNewListingByLocation(location, daysonzillow):
    curpage = 1
    maxpage = 2
    houseresult = []
    while maxpage > curpage:

        querystring = {"location": location + ", wa", "page": str(curpage), "status": "forSale",
                       "doz": str(daysonzillow)}
        response = requests.get(url, headers=headers, params=querystring)
        time.sleep(0.5)
        result = response.json()
        if response.status_code == 502:
            warn('502 on ' + location)
            return houseresult
        try:
            houseresult = houseresult + result['results']
            curpage = curpage + 1
            print(curpage)
            maxpage = result['totalPages']
        except Exception as e:
            warn(e.__str__())
            return houseresult
    return houseresult

def SearchZillowNewListingByInterest(location, beds_min,beds_max,baths_min,price_max,daysonzillow):
    curpage = 1
    maxpage = 2
    houseresult = []
    while maxpage > curpage:

        querystring = {"location": location + ", wa", "page": str(curpage),
                       "status": "forSale",
                       "price_max": price_max,
                       "beds_min": beds_min,
                       "beds_max":beds_max,
                       "baths_min": baths_min,
                       # "doz": str(daysonzillow)
                       }

        response = requests.get(url, headers=headers, params=querystring)
        time.sleep(0.5)
        result = response.json()
        if response.status_code == 502:
            warn('502 on ' + location)
            return houseresult
        try:
            houseresult = houseresult + result['results']
            print(location, curpage)
            curpage = curpage + 1
            maxpage = result['totalPages']
        except Exception as e:
            warn(e.__str__())
            return houseresult
    return houseresult



def SearchZillowHomesByLocation(location, status="recentlySold", doz=14, timeOnZillow=14):
    houseresult = []
    print(f'Searching {status} homes in location: {location}')

    interval = 1000
    minhomesize = 0
    maxhomesize = interval + minhomesize

    seen_ids = set()
    max_sqft = 10000
    min_interval = 50

    while True:
        lastpage = 1
        maxpage = 2
        results_in_this_interval = []
        should_restart = False  # Flag to control outer loop

        while maxpage >= lastpage:
            querystring = {
                "location": f"{location}, WA",
                "page": str(lastpage),
                "status": status,
                "output": "json",
                "listing_type": "by_agent",
                "sqft_min": str(minhomesize),
                "sqft_max": str(maxhomesize),
                "doz": doz if status == "recentlySold" else doz,
                "timeOnZillow": timeOnZillow if status == "forSale" else None,
                "isMultiFamily": "false",
                "sortSelection":"priorityscore"
            }
            querystring = {k: v for k, v in querystring.items() if v is not None}

            print(f"Search {minhomesize}–{maxhomesize} sqft, page {lastpage}, status={status}")
            response = requests.get(url, headers=headers, params=querystring)
            time.sleep(1.0)

            if response.status_code == 502:
                warn(f'502 error on {location}')
                should_restart = True
                break

            try:
                result = response.json()
                maxpage = result.get('totalPages', 0)
                if maxpage!=0:
                    maxpagebackup = maxpage
                results_in_this_interval.extend(result.get('results', []))
                print(f'Page {lastpage} of {maxpage} processed.')
                lastpage += 1

                if maxpage ==0:
                    maxpage= maxpagebackup
                    print('No results found.')

                if maxpage >= 20:
                    print("Search too large for interval, reducing...")
                    interval = max(min_interval, interval // 2)
                    maxhomesize = minhomesize + interval
                    should_restart = True
                    break  # break inner, continue outer
            except Exception as e:
                print("Search Zillow failed due to an exception:", e)
                break

        if should_restart:
            continue  # restart outer loop with adjusted interval

        if maxhomesize >= max_sqft:
            print("All intervals processed.")
            break

        for listing in results_in_this_interval:
            zpid = listing.get('zpid')
            if zpid and zpid not in seen_ids:
                seen_ids.add(zpid)
                houseresult.append(listing)
        print(f'Found {len(houseresult)} unique results.')

        # Move to the next range with small overlap
        minhomesize = maxhomesize
        maxhomesize = min(minhomesize + interval, max_sqft)



    return houseresult


def SearchZillowHomesByLocationbackup(location, status="recentlySold", doz=14, timeOnZillow=14):
    houseresult = []
    print(f'Searching {status} homes in location: {location}')

    interval = 10000
    minhomesize = 0
    maxhomesize = interval + minhomesize

    while True:
        lastpage = 1
        maxpage = 2
        results_in_this_interval = []

        while maxpage >= lastpage:
            querystring = {
                "location": f"{location}, WA",
                "page": str(lastpage),
                "status": status,
                "output": "json",
                # "sortSelection": "priorityscore",
                "listing_type": "by_agent",
                "sqft_min": str(minhomesize),
                "sqft_max": str(maxhomesize),
                "doz": doz if status == "recentlySold" else doz,
                "timeOnZillow": timeOnZillow if status == "forSale" else None,
                "isMultiFamily": "false",
            }
            querystring = {k: v for k, v in querystring.items() if v is not None}

            print(f"Search {minhomesize} to {maxhomesize} with status{status}.")
            response = requests.get(url, headers=headers, params=querystring)
            time.sleep(0.5)

            if response.status_code == 502:
                warn(f'502 error on {location}')
                break

            try:
                result = response.json()


                if result.get('totalPages') >= 20:
                    print("Search too large, reducing interval.")
                    interval //= 2
                    maxhomesize = minhomesize + interval  # Adjust the range
                    continue  # Restart the outer loop with updated interval
                maxpage = result.get('totalPages')
                results_in_this_interval.extend(result.get('results', []))
                print(f'Page {lastpage} of {maxpage} processed.')
                lastpage += 1

            except Exception as e:
                print("Search Zillow failed due to an exception:", e)
                break

        houseresult.extend(results_in_this_interval)

        # Check if interval is small enough or search is complete
        if maxpage < 20:
            if interval == 1:
                print("Search complete with current interval.")
                break

        if maxpage < 3:
            interval = 2*interval



        # Move to the next range
        if maxpage <= 20 and minhomesize + interval >= 10000:  # Arbitrary max size for demonstration
            print("All intervals processed.")
            break

        minhomesize = maxhomesize
        maxhomesize = minhomesize + interval

    print(f'Found {len(houseresult)} results.')
    return houseresult





def SearchZillowHomesByZone(zone, status="recentlySold", doz=14, timeOnZillow=14):
    houseresult = []
    print(f'Searching {status} homes in zone: {zone.zonename()}')
    polygonurl = "https://zillow56.p.rapidapi.com/search_polygon"
    interval = 10000
    minhomesize = 0
    maxhomesize = interval + minhomesize

    while True:
        lastpage = 1
        maxpage = 2
        results_in_this_interval = []

        while maxpage >= lastpage:
            querystring = {
                "polygon": zone.get_polygon_string(),
                     "page": str(lastpage),
                "status": status,
                "output": "json",
                # "sortSelection": "priorityscore",
                "listing_type": "by_agent",
                "sqft_min": str(minhomesize),
                "sqft_max": str(maxhomesize),
                "doz": doz if status == "recentlySold" else doz,
                "timeOnZillow": timeOnZillow if status == "forSale" else None,
                "isMultiFamily": "false",
            }


            querystring = {k: v for k, v in querystring.items() if v is not None}

            print(f"Search {minhomesize} to {maxhomesize} with status{status}.")
            response = requests.get(polygonurl, headers=headers, params=querystring)
            time.sleep(0.5)

            if response.status_code == 502:
                warn(f'502 error on {zone.zonename()}')
                break

            try:
                result = response.json()


                if result.get('totalPages') >= 20:
                    print("Search too large, reducing interval.")
                    interval //= 2
                    maxhomesize = minhomesize + interval  # Adjust the range
                    continue  # Restart the outer loop with updated interval
                maxpage = result.get('totalPages')
                results_in_this_interval.extend(result.get('results', []))
                print(f'Page {lastpage} of {maxpage} processed.')
                lastpage += 1

            except Exception as e:
                print("Search Zillow failed due to an exception:", e)
                break

        houseresult.extend(results_in_this_interval)

        # Check if interval is small enough or search is complete
        if maxpage < 20:
            if interval == 1:
                print("Search complete with current interval.")
                break

        if maxpage < 3:
            interval = 2*interval



        # Move to the next range
        if maxpage <= 20 and minhomesize + interval >= 10000:  # Arbitrary max size for demonstration
            print("All intervals processed.")
            break

        minhomesize = maxhomesize
        maxhomesize = minhomesize + interval

    print(f'Found {len(houseresult)} results.')
    return houseresult

def SearchZillowHomesFSBO(city, lastpage, maxpage, status="forSale", duration=14):

    houseresult=[]
    print('Search in location ' + status + ' : ', city)
    # lastpage = 1
    # maxpage = 2

    querystring = {"location":city + ", wa","page": str(lastpage),"status": status,
                   "listing_type": "by_owner_other",
                   "isForSaleByOwner": "true"}
    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)
    if response.status_code==502:
        raise('502 on ' + city)
    try:
        result = response.json()
        houseresult = houseresult+ result['results']
        maxpage = result['totalPages']
        print('lastpage:' + str(lastpage) + ' out of ' + str(maxpage))
        lastpage = lastpage + 1
    except Exception as e:
        raise(f"Search Zillow failed due to an exception")




    return houseresult, lastpage, maxpage
# def UpdateListfromLocation(location):
#     querystring = {"location":location + ", wa","status":"recentlySold","doz":"30"}
#     response = requests.get(url, headers=headers, params=querystring)
#     result = response.json()
#
#     houseresult = result['results']
#     i=1
#     while result['totalPages']>i:
#         querystring = {"location": location + ", wa", "page": str(i+1),"status": "recentlySold", "doz": "30"}
#         response = requests.get(url, headers=headers, params=querystring)
#         result = response.json()
#         houseresult = houseresult+ result['results']
#         i=i+1
#
#     dbmethods.SaveHouseSearchDataintoDB(houseresult)
#     return dbmethods.AllListigs()

# def addHomesToDB():
#     csv_file_path = 'path_to_your_csv_file.csv'
#
#     # Connect to the SQLite database
#     conn = sqlite3.connect('listings.db')
#     cursor = conn.cursor()
#
#     # Open the CSV file and read its contents
#     with open(csv_file_path, 'r') as csv_file:
#         csv_reader = csv.reader(csv_file)
#
#         # Skip header (if it exists)
#         next(csv_reader)
#
#         # Insert each row into the database
#         for row in csv_reader:
#             # Assuming the CSV columns match the database table columns
#             cursor.execute("INSERT INTO Listing (api_id, added_on) VALUES (?, ?)", (row[0], row[1]))
#
#     # Commit the changes and close the connection
#     conn.commit()
#     conn.close()





# def searchZillow():
#     with open('../../data.txt', "r") as file:
#         responseobject = json.load(file)
#
#     results = responseobject['results']
#     all_fields = set()
#     for result in results:
#         all_fields.update(result.keys())
#
#     # Step 2 & 3: Use these fields as the CSV headers and write each result to the CSV.
#     with open('../../data.csv', 'w', newline='') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=all_fields)
#         writer.writeheader()
#         for row in results:
#             writer.writerow(row)
#     return responseobject