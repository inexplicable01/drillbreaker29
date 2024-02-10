import requests
import json
from datetime import datetime
import csv
from warnings import warn
import folium

url = "https://zillow56.p.rapidapi.com/search"
rapidapikey = "0f1a70c877msh63c2699008fda33p17811djsn4ef183cca70a"
headers = {
    "X-RapidAPI-Key": rapidapikey,
    "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
}

location = 'seattle'
curpage = 1
maxpage = 2
houseresult = []
daysonzillow=7
while maxpage > curpage:
    querystring = {"location": location + ", wa", "page": str(curpage), "status": "forSale", "doz": str(daysonzillow)}
    response = requests.get(url, headers=headers, params=querystring)
    result = response.json()
    if response.status_code == 502:
        warn('502 on ' + location)
        break
    houseresult = houseresult + result['results']
    curpage = curpage + 1
    print(curpage)
    maxpage = result['totalPages']


print(houseresult)
TR = [47.71008,-122.237]
TL = [47.71008,-122.428]
BR = [47.62454,-122.237]
BL = [47.62454,-122.428]
filtered_houses = []
for house in houseresult:
    # Check if the house's coordinates fall within the defined bounding box
    if (BL[0] <= house['latitude'] <= TL[0]) and (TL[1] <= house['latitude'] <= TR[1]):
        filtered_houses.append(house)
# Calculate the center of your bounding box (average of the bounding box coordinates)
center_lat = (TL[0] + BR[0]) / 2
center_lon = (TL[1] + TR[1]) / 2

# Create a map centered at the calculated coordinates
m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

# print(response.json())
for house in filtered_houses:
    folium.Marker(
        [house['latitude'], house['latitude']],
        popup=f"House: Lat {house['latitude']}, Lon {house['latitude']}"
    ).add_to(map)

map
pp=3