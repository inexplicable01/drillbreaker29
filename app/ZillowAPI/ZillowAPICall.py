import requests
import os
from warnings import warn

import sqlite3
url = "https://zillow56.p.rapidapi.com/search"
zpidurl = "https://zillow56.p.rapidapi.com/property"
keystokeep = ['zpid','price','unit','streetAddress',
              'city','state','zipcode','bedrooms',
              'bathrooms','zestimate','daysOnZillow',
              'dateSold','homeType','latitude','longitude']

headers = {
    "X-RapidAPI-Key": os.getenv('RAPID_API_KEY'),
    "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
}
# from app.DataBaseFunc import dbmethods




def SearchZillowByZPID(ZPID):
    querystring = {"zpid": ZPID}
    response = requests.get("https://zillow56.p.rapidapi.com/property", headers=headers, params=querystring)
    try:
        return response.json()
    except Exception as e:
        return None

def SearchZillowByAddress(addressStr):
    # querystring = {"location":location + ", wa","page": str(lastpage),"status":"forSale","doz":"14"}
    querystring = {"address": addressStr}
    response = requests.get("https://zillow56.p.rapidapi.com/search_address", headers=headers, params=querystring)
    if response.status_code==502:
        warn('502 on ' + addressStr)
    try:
        return response.json()
    except Exception as e:
        return None


# def loadcsv(Listing, db):
#     with open('../../data.csv', 'r') as file:
#         reader = csv.DictReader(file)
#         data = list(reader)
#     dbmethods.loadHouseSearchDataintoDB(data, Listing, db)
#     return data
def SearchZillowNewListingByLocation(location, daysonzillow):
    curpage = 1
    maxpage = 2
    houseresult = []
    while maxpage > curpage:

        querystring = {"location": location + ", wa", "page": str(curpage), "status": "forSale",
                       "doz": str(daysonzillow)}
        response = requests.get(url, headers=headers, params=querystring)
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
            warn(e)
            return houseresult
    return houseresult

def SearchZillowSoldHomesByLocation(location, duration=14):

    lastpage = 1
    maxpage = 2
    houseresult=[]
    while maxpage>lastpage:
        querystring = {"location":location + ", wa","page": str(lastpage),"status":"recentlySold","doz":str(duration)}
        response = requests.get(url, headers=headers, params=querystring)
        result = response.json()
        if response.status_code==502:
            warn('502 on ' + location)
            break
        try:
            houseresult = houseresult+ result['results']
            lastpage=lastpage+1
            maxpage = result['totalPages']
        except Exception as e:
            warn('Search Zillow failed',e)
    return houseresult
    # dbmethods.SaveHouseSearchDataintoDB(houseresult)


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