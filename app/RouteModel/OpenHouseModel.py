import folium
# from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForOpenHouse
from app.EmailHelper.EmailSender import send_email
from app.EmailHelper.EmailContentGenerator import BodyNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller

defaultrecipient = 'waichak.luk@gmail.com'





# def SearchForOpenHousesOld():
#     TR = [47.71008, -122.237]
#     TL = [47.71008, -122.428]
#     BR = [47.62454, -122.237]
#     BL = [47.62454, -122.428]
#     center_lat = (TL[0] + BR[0]) / 2
#     center_lon = (TL[1] + TR[1]) / 2
#     openhouse_propertydata = ZillowSearchForOpenHouse(TR,TL,BR,BL)
#     send_email(subject='NewListing',
#                html_content=BodyNewListing(openhouse_propertydata),
#                recipient =defaultrecipient)
#
#     return maplistings(openhouse_propertydata,center_lat,center_lon), openhouse_propertydata


def SearchForOpenHouses():

    openhouse_brieflistings = brieflistingcontroller.OpenHousePotential()
    # send_email(subject='NewListing',
    #            html_content=BodyNewListing(openhouse_propertydata),
    #            recipient=defaultrecipient)

    return maplistings(openhouse_brieflistings), openhouse_brieflistings






def maplistings(brieflistings):
    center_lat, center_lon = calculate_center_coordinates(brieflistings)

    map = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = map.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    for brieflisting in brieflistings:

        days = brieflisting.daysOnZillow
        if days < 7:
            color = 'red'
        elif 7 <= days < 14:
            color = 'orange'
        elif 14 <= days < 21:
            color = 'green'
        else:
            color = 'blue'
        htmltext = f"<a href='https://www.zillow.com{brieflisting.hdpUrl}' target='_blank'>House Link</a>" \
               f"<br/>" \
               f"Price {brieflisting.price}<br/>" \
               f"Beds {brieflisting.bedrooms} Bath {brieflisting.bathrooms}<br/>" \
               f"Square ft {brieflisting.livingArea}<br/>" \
               f"Days on Market {brieflisting.daysOnZillow}<br/>"

        popup = folium.Popup(htmltext, max_width=300)

        icon = folium.Icon(color=color)

        folium.Marker(
            location=[brieflisting.latitude, brieflisting.longitude],
            popup=popup,
            icon =icon
        ).add_to(map)
    map_html = map._repr_html_()

    return map_html


def calculate_center_coordinates(brieflistings):
    """
    Calculate the center latitude and longitude from an array of brieflistings.

    :param brieflistings: List of dictionaries with 'latitude' and 'longitude' keys
    :return: Tuple of (center_lat, center_lon)
    """
    if not brieflistings:
        raise ValueError("The brieflistings array is empty.")

    total_lat = 0
    total_lon = 0
    count = len(brieflistings)

    for listing in brieflistings:
        total_lat += listing.latitude
        total_lon += listing.longitude

    center_lat = total_lat / count
    center_lon = total_lon / count

    return center_lat, center_lon

