import folium
from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForOpenHouse
from app.EmailHelper.EmailSender import send_email
from app.EmailHelper.EmailContentGenerator import BodyNewListing
defaultrecipient = 'waichak.luk@gmail.com'
def SearchForOpenHouses():
    TR = [47.71008, -122.237]
    TL = [47.71008, -122.428]
    BR = [47.62454, -122.237]
    BL = [47.62454, -122.428]
    center_lat = (TL[0] + BR[0]) / 2
    center_lon = (TL[1] + TR[1]) / 2
    openhouse_propertydata = ZillowSearchForOpenHouse(TR,TL,BR,BL)

    map = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = map.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    for propertydata in openhouse_propertydata:

        days = propertydata['daysOnZillow']
        if days < 7:
            color = 'red'
        elif 7 <= days < 14:
            color = 'orange'
        elif 14 <= days < 21:
            color = 'green'
        else:
            color = 'blue'
        htmltext = f"<a href='https://www.zillow.com{propertydata['hdpUrl']}' target='_blank'>House Link</a>" \
               f"<br/>" \
               f"Price {propertydata['price']}<br/>" \
               f"Beds {propertydata['bedrooms']} Bath {propertydata['bathrooms']}<br/>" \
               f"Square ft {propertydata['livingArea']}<br/>" \
               f"Days on Market {propertydata['daysOnZillow']}<br/>" \
               f"Agent Name {propertydata['attributionInfo']['agentName']}<br/>" \
               f"Agent Number {propertydata['attributionInfo']['agentPhoneNumber']}<br/>" \
               f"Neighbour {propertydata['neighborhoodRegion']['name']}<br/>"

        popup = folium.Popup(htmltext, max_width=300)

        icon = folium.Icon(color=color)

        folium.Marker(
            location=[propertydata['latitude'], propertydata['longitude']],
            popup=popup,
            icon =icon
        ).add_to(map)
    map_html = map._repr_html_()

    send_email(subject='NewListing',
               html_content=BodyNewListing(openhouse_propertydata),
               recipient =defaultrecipient)

    return map_html, openhouse_propertydata