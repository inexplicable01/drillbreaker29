import requests
import json
from datetime import datetime
import csv
from warnings import warn
from app.config import Config
# from app.models import SaveHouseSearchDataintoDB
url = "https://zillow56.p.rapidapi.com/search"
zpidurl = "https://zillow56.p.rapidapi.com/property"
# from datetime import datetime
import sqlite3
keystokeep = ['zpid','price','unit','streetAddress',
              'city','state','zipcode','bedrooms',
              'bathrooms','zestimate','daysOnZillow',
              'dateSold','homeType','latitude','longitude']
rapidapikey = "0f1a70c877msh63c2699008fda33p17811djsn4ef183cca70a"
# from app.useful_func import safe_int_conversion,safe_float_conversion

headers = {
    "X-RapidAPI-Key": rapidapikey,
    "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
}
from app.DataBaseFunc import dbmethods

def searchZillow():
    # timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # filename = f"data_{timestamp}.txt"
    # querystring = {"location":"seattle, wa","status":"recentlySold"}
    #
    # headers = {
    #     "X-RapidAPI-Key": "ade2517b07msha8401ba0c4f1ac2p189937jsn03f85bb20c18",
    #     "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
    # }
    #
    # response = requests.get(url, headers=headers, params=querystring)
    #
    # responseobject = response.json()

    # with open(filename, "w") as file:
    #     json.dump(responseobject, file)

    with open('../data.txt', "r") as file:
        responseobject = json.load(file)

    results = responseobject['results']
    all_fields = set()
    for result in results:
        all_fields.update(result.keys())

    # Step 2 & 3: Use these fields as the CSV headers and write each result to the CSV.
    with open('../data.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    return responseobject


def SearchListingByZPID(ZPID):
    url = "https://zillow56.p.rapidapi.com/property"

    querystring = {"zpid": ZPID}
    response = requests.get(url, headers=headers, params=querystring)

    # print(response.json())
    try:
        return response.json()
    except Exception as e:
        return None


def loadcsv(Listing, db):
    with open('../data.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    dbmethods.loadHouseSearchDataintoDB(data, Listing, db)
    return data

def SearchNewListing(location, daysonzillow):
    curpage = 1
    maxpage = 2
    houseresult=[]
    while maxpage>curpage:
        querystring = {"location":location + ", wa","page": str(curpage),"status":"forSale","doz":str(daysonzillow)}
        response = requests.get(url, headers=headers, params=querystring)
        result = response.json()
        if response.status_code==502:
            warn('502 on ' + location)
            break
        houseresult = houseresult+ result['results']
        curpage=curpage+1
        maxpage = result['totalPages']
    dbmethods.loadHouseSearchDataintoDB(houseresult, 'forSale')
    return houseresult

def SearchProperty(addressStr):
    # querystring = {"location":location + ", wa","page": str(lastpage),"status":"forSale","doz":"14"}
    querystring = {"address": addressStr}
    url = "https://zillow56.p.rapidapi.com/search_address"
    response = requests.get(url, headers=headers, params=querystring)
    result = response.json()
    if response.status_code==502:
        warn('502 on ' + addressStr)
    return result

def SearchNewSoldHomes(location, duration="14"):

    lastpage = 1
    maxpage = 2
    houseresult=[]
    while maxpage>lastpage:
        querystring = {"location":location + ", wa","page": str(lastpage),"status":"recentlySold","doz":duration}
        headers = {
            "X-RapidAPI-Key": rapidapikey,
            "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        result = response.json()
        if response.status_code==502:
            warn('502 on ' + location)
            break
        houseresult = houseresult+ result['results']
        lastpage=lastpage+1
        maxpage = result['totalPages']
    dbmethods.SaveHouseSearchDataintoDB(houseresult)


def UpdateListfromLocation(location):
    querystring = {"location":location + ", wa","status":"recentlySold","doz":"30"}
    headers = {
        "X-RapidAPI-Key": rapidapikey,
        "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    result = response.json()


    houseresult = result['results']
    i=1

    while result['totalPages']>i:
        querystring = {"location": location + ", wa", "page": str(i+1),"status": "recentlySold", "doz": "30"}
        headers = {
            "X-RapidAPI-Key": rapidapikey,
            "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        result = response.json()
        houseresult = houseresult+ result['results']
        i=i+1


    dbmethods.SaveHouseSearchDataintoDB(houseresult)
    return dbmethods.AllListigs()

def addHomesToDB():
    csv_file_path = 'path_to_your_csv_file.csv'

    # Connect to the SQLite database
    conn = sqlite3.connect('listings.db')
    cursor = conn.cursor()

    # Open the CSV file and read its contents
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip header (if it exists)
        next(csv_reader)

        # Insert each row into the database
        for row in csv_reader:
            # Assuming the CSV columns match the database table columns
            cursor.execute("INSERT INTO Listing (api_id, added_on) VALUES (?, ?)", (row[0], row[1]))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def ZillowSearchForOpenHouse():

    location = 'seattle'
    curpage = 1
    maxpage = 2
    houseresult = []
    daysonzillow = 30
    while maxpage > curpage:
        querystring = {"location": location + ", wa", "page": str(curpage), "status": "forSale",
                       "doz": str(daysonzillow)}
        response = requests.get(url, headers=headers, params=querystring)
        result = response.json()
        if response.status_code == 502:
            warn('502 on ' + location)
            break
        houseresult = houseresult + result['results']
        curpage = curpage + 1
        print(curpage)
        maxpage = result['totalPages']

    TR = [47.71008, -122.237]
    TL = [47.71008, -122.428]
    BR = [47.62454, -122.237]
    BL = [47.62454, -122.428]
    filtered_houses = []
    for house in houseresult:

        # Check if the house's coordinates fall within the defined bounding box
        if (BL[0] <= house['latitude'] <= TL[0]) and (TL[1] <= house['longitude'] <= TR[1]):

            response = SearchListingByZPID(house['zpid'])

            print('address',response['address']['streetAddress'])
            print('isOpenHouse',response['listingSubType']['isOpenHouse'])
            print('openHouseSchedule',response['openHouseSchedule'])
            print('homeType', response['homeType'])
            print('propertyCondition', response['resoFacts']['propertyCondition'])
            print('neighborhoodRegion', response['neighborhoodRegion'])
            # neighborhoodRegion
            if response['homeType']=="LOT" or response['homeType']=="MULTI_FAMILY" or response['homeType']=="CONDO":
                print('Not a proper home Type, skip')
                continue
            if response['resoFacts']['propertyCondition']=="Under Construction":
                print('Under Construction, skip')
                continue
            if response['neighborhoodRegion']['name']  in Config.WRONGNEIGHBORHOODS:
                print('wrong neighbourhood, skip')
                continue


            if not response['listingSubType']['isOpenHouse']:
                filtered_houses.append(response)


    # Calculate the center of your bounding box (average of the bounding box coordinates)
    center_lat = (TL[0] + BR[0]) / 2
    center_lon = (TL[1] + TR[1]) / 2




    return filtered_houses,center_lat,center_lon