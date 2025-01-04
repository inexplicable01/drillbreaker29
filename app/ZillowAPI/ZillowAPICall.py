import requests
import os
from warnings import warn
import time
from app.DBModels.BriefListing import BriefListing
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

# def SearchZillowHomesByLocation(location, status="recentlySold", doz=14, duration=14):
#     houseresult=[]
#     print('Search in location ' + status + ' : ', location)
#     lastpage = 1
#     maxpage = 2
#
#     interval=10000
#     minhomesize=1
#     maxhomesize=interval+minhomesize
#
#     while maxpage>lastpage:
#         querystring = {
#             "location": f"{location}, wa",
#             "page": str(lastpage),
#             "status": status,
#             "sqft_min": str(minhomesize),
#             "sqft_max": str(maxhomesize),
#             "doz": doz if status == "recentlySold" else None,
#             "timeOnZillow": duration if status == "forSale" else None,
#             "isMultiFamily": "false",
#         }
#         querystring = {k: v for k, v in querystring.items() if v is not None}
#
#
#         response = requests.get(url, headers=headers, params=querystring)
#
#         time.sleep(0.5)
#         if response.status_code==502:
#             warn('502 on ' + location)
#             break
#         try:
#             result = response.json()
#             maxpage =result['totalPages']
#             if maxpage >= 20:
#                 print("search too large, set interval to half")
#                 ### go back to query string building.
#             houseresult = houseresult+ result['results']
#             maxpage = result['totalPages']
#             print('lastpage:' + str(lastpage) + ' out of ' + str(maxpage))
#             lastpage = lastpage + 1
#
#         except Exception as e:
#             print(f"Search Zillow failed due to an exception")
#             break
#     print('found ', len(houseresult), ' results')
#     return houseresult



def SearchZillowHomesByLocation(location, status="recentlySold", doz=14, duration=14):
    houseresult = []
    print(f'Searching {status} homes in location: {location}')

    interval = 10000
    minhomesize = 1
    maxhomesize = interval + minhomesize

    while True:
        lastpage = 1
        maxpage = 2
        results_in_this_interval = []

        while maxpage >= lastpage:
            querystring = {
                "location": f"{location}, wa",
                "page": str(lastpage),
                "status": status,
                "sqft_min": str(minhomesize),
                "sqft_max": str(maxhomesize),
                "doz": doz if status == "recentlySold" else None,
                "timeOnZillow": duration if status == "forSale" else None,
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


def SearchZillowHomesByCity(city, lastpage, maxpage, status="forSale", duration=14):
    #Brief Listing

    houseresult=[]
    print('Search in location ' + status + ' : ', city)
    # lastpage = 1
    # maxpage = 2

    querystring = {"location":city + ", wa","page": str(lastpage),"status": status}
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

    forsalebrieflistingarr = []
    for briefhomedata in houseresult:
            forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None,None,city))
    return forsalebrieflistingarr, lastpage, maxpage

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

    brieflistingarr = []
    for briefhomedata in houseresult:
        if 'is_forAuction' in briefhomedata['listing_sub_type'].keys():
            continue
        # print(briefhomedata['listing_sub_type'])
        brieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None,None,city))


    return brieflistingarr, lastpage, maxpage
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