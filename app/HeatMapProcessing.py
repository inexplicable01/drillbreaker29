import folium
from folium.plugins import HeatMap
from app.models import AllListings
from datetime import datetime, timedelta


SOLDHOTTNESS = 'SOLDHOTTNESS'
EXPENSIVEHOME =  'EXPENSIVEHOME'
def HouseSoldSpeed(list2pend):
    if list2pend==0:
        return 0.1
    if list2pend<3:
        return 1
    if list2pend<7:
        return 0.8
    if list2pend<14:
        return 0.6
    if list2pend<30:
        return 0.4
    if list2pend<60:
        return 0.2
    return 0.1

def HeatMapGen(days, displayfun):
    current_date = datetime.now()
    days_ago = current_date - timedelta(days=days)
    coords=[]
    lat=0
    long=0
    listings = AllListings()
    if displayfun==SOLDHOTTNESS:
        for listing in listings:
            if  days_ago <= listing.dateSold <= current_date:
                coords.append([listing.latitude, listing.longitude, HouseSoldSpeed(listing.list2pend)])
                lat = lat + listing.latitude
                long = long + listing.longitude
    elif displayfun==EXPENSIVEHOME:
        for listing in listings:
            if  days_ago <= listing.dateSold <= current_date:
                if listing.price<2000000:
                    coords.append([listing.latitude, listing.longitude])
                    lat = lat + listing.latitude
                    long = long + listing.longitude
    if len(coords)==0:
        m = folium.Map(location=[47.608013, -122.335167], zoom_start=13)
        HeatMap(coords).add_to(m)
        m = m._repr_html_()
        return m
    lat = lat/len(coords)
    long = long / len(coords)
    m = folium.Map(location=[lat, long], zoom_start=13)

    # Add the heat map layer to the map
    HeatMap(coords).add_to(m)
    m = m._repr_html_()
    return m , len(coords)


def WhereExpensiveHomes(minprice, days=60):
    current_date = datetime.now()
    days_ago = current_date - timedelta(days=days)
    coords=[]
    lat=0
    long=0
    listings = AllListings()
    for listing in listings:
        if  days_ago <= listing.dateSold <= current_date:
            if listing.price>minprice:
                coords.append([listing.latitude, listing.longitude])
                lat = lat + listing.latitude
                long = long + listing.longitude
    if len(coords)==0:
        m = folium.Map(location=[47.608013, -122.335167], zoom_start=13)
        HeatMap(coords).add_to(m)
        m = m._repr_html_()
        return m
    lat = lat/len(coords)
    long = long / len(coords)
    m = folium.Map(location=[lat, long], zoom_start=13)

    # Add the heat map layer to the map
    HeatMap(coords).add_to(m)
    m = m._repr_html_()
    return m