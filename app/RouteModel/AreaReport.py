import folium
from app.ZillowDataProcessor import SearchZillowNewListingByLocation,SearchZillowByAddress
from app.DataBaseFunc import dbmethods
from app.ZillowAPI.ZillowAPICall import SearchZillowSoldHomesByLocation
from app.ZillowAPI.ZillowHandler import ListingLengthbyBriefListing, FindSoldHomesByLocation
import pandas as pd
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
from joblib import load
import os
import json
# model = load('linear_regression_model.joblib')

def AreaReport(locations):
    housesoldpriceaverage = initiateSummarydata()
    soldhomes=[]
    for location in locations:
        soldhomes=  soldhomes+ FindSoldHomesByLocation(location,30)


    for brieflisting in soldhomes:
        listresults = ListingLengthbyBriefListing(brieflisting)
        brieflisting.updateListingLength(listresults)
        # print(brieflisting.ref_address())
        # print(listresults)
        try:
            bedbathcode = int(brieflisting.bedrooms)+float(brieflisting.bathrooms)*100
            if 101<=bedbathcode<=102:
                housesoldpriceaverage["1bed1bath"]["count"] +=1
                housesoldpriceaverage["1bed1bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["1bed1bath"]["houses"].append(brieflisting)
            elif 201.5<=bedbathcode<=202.5:
                housesoldpriceaverage["2bed2bath"]["count"] +=1
                housesoldpriceaverage["2bed2bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["2bed2bath"]["houses"].append(brieflisting)
            elif 302 <= bedbathcode <= 302.5:
                housesoldpriceaverage["3bed2bath"]["count"] +=1
                housesoldpriceaverage["3bed2bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["3bed2bath"]["houses"].append(brieflisting)
            elif 302.5 < bedbathcode <= 304:
                housesoldpriceaverage["3bed3bath"]["count"] +=1
                housesoldpriceaverage["3bed3bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["3bed3bath"]["houses"].append(brieflisting)
            elif 400 <= bedbathcode <= 402:
                housesoldpriceaverage["4bed2-bath"]["count"] +=1
                housesoldpriceaverage["4bed2-bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["4bed2-bath"]["houses"].append(brieflisting)
            elif 402 < bedbathcode <= 404:
                housesoldpriceaverage["4bed3+bath"]["count"] +=1
                housesoldpriceaverage["4bed3+bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["4bed3+bath"]["houses"].append(brieflisting)
        except Exception as e:
            print('Error with ', brieflisting)
    # Create a map centered around Ballard, Seattle

    for key, value in housesoldpriceaverage.items():
        value['minprice']=1000000000
        value['maxprice']=0
        if value['count']==0:
            value['aveprice'] = 'NA'
        else:
            value['aveprice']= int(value['totalprice']/value['count'])
        for brieflisting in value["houses"]:
            if brieflisting.price<value['minprice']:
                value['minprice'] = brieflisting.price
            if brieflisting.price>value['maxprice']:
                value['maxprice'] = brieflisting.price




    return generateMap(soldhomes, location), soldhomes,housesoldpriceaverage


def initiateSummarydata():
    return{
        "1bed1bath": {
            "beds": 1,
            "baths": 1,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "2bed2bath": {
            "beds": 2,
            "baths": 2,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "3bed2bath": {
            "beds": 3,
            "baths": 2,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "3bed3bath": {
            "beds": 3,
            "baths": 3,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "4bed2-bath": {
            "beds": 4,
            "baths": 2,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "4bed3+bath": {
            "beds": 4,
            "baths": 3,
            "count": 0,
            "totalprice": 0,
            "houses": []
        }
    }

def generateMap(soldhomes, location):
    m = folium.Map(location=[47.6762, -122.3860], zoom_start=13)
    ballard_coordinates = [
        (47.69062, -122.36616),  # Example coordinate 4
        (47.67608, -122.36608),  # Example coordinate 4
        (47.67601, -122.36072),
        (47.66145, -122.36072),
        (47.66484, -122.39476),
        (47.66869, -122.40460),
        (47.67661, -122.40994),
        (47.69051, -122.40387),
    ]
    # Create a polygon over Ballard and add it to the map
    folium.Polygon(locations=ballard_coordinates, color='blue', fill=True, fill_color='blue').add_to(m)
    fremont_coordinates = [
        (47.66685, -122.36071),
        (47.66216, -122.35405),
        (47.66509, -122.35387),
        (47.66505, -122.34708),
        (47.65659, -122.34738),
        (47.65655, -122.34238),
        (47.64809, -122.34238),
        (47.65659, -122.36714),
        (47.66136, -122.36625),
        (47.66148, -122.36089),

    ]
    # Create a polygon over Ballard and add it to the map
    folium.Polygon(locations=fremont_coordinates, color='green', fill=True, fill_color='green').add_to(m)
    wallingford_coordinates = [
        (47.66504, -122.34709),
        (47.66516, -122.34014),
        (47.67018, -122.33971),
        (47.67244, -122.33370),
        (47.67227, -122.32169),
        (47.65365, -122.32280),
        (47.64787, -122.34246),
        (47.65677, -122.34229),
        (47.66516, -122.34014),
        (47.65654, -122.34709),
    ]
    # Create a polygon over Ballard and add it to the map
    folium.Polygon(locations=wallingford_coordinates, color='green', fill=True, fill_color='green').add_to(m)
    # map = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = m.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    for brieflisting in soldhomes:
        list2penddays = brieflisting.list2penddays
        if list2penddays is None:
            color = 'gray'
        else:
            if list2penddays < 7:
                color = 'red'
            elif 7 <= list2penddays < 14:
                color = 'orange'
            elif 14 <= list2penddays < 21:
                color = 'green'
            else:
                color = 'blue'
        htmltext = f"Price {brieflisting.price}<br/>" \
               f"Beds {brieflisting.bedrooms} Bath {brieflisting.bathrooms}<br/>" \
               f"Square ft {brieflisting.livingArea}<br/>" \
               f"List to Contract {brieflisting.list2penddays}<br/>"

        # f"<a href='https://www.zillow.com{house['hdpUrl']}' target='_blank'>House Link</a>" \
        # f"<br/>" \
        popup = folium.Popup(htmltext, max_width=300)

        icon = folium.Icon(color=color)

        folium.Marker(
            location=[brieflisting.latitude, brieflisting.longitude],
            popup=popup,
            icon =icon
        ).add_to(m)

    map_html = m._repr_html_()
    return map_html

# def ListingLength(soldhouse, Listing, db):
#
#     if soldhouse.list2pendCheck==0

