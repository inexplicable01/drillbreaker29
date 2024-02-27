import folium
from app.ZillowDataProcessor import ZillowSearchForOpenHouse
def SearchForOpenHouses():
    TR = [47.71008, -122.237]
    TL = [47.71008, -122.428]
    BR = [47.62454, -122.237]
    BL = [47.62454, -122.428]
    center_lat = (TL[0] + BR[0]) / 2
    center_lon = (TL[1] + TR[1]) / 2
    filtered_houses = ZillowSearchForOpenHouse(TR,TL,BR,BL)
    # infodump = []
    map = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = map.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    for house in filtered_houses:

        days = house['daysOnZillow']
        if days < 7:
            color = 'red'
        elif 7 <= days < 14:
            color = 'orange'
        elif 14 <= days < 21:
            color = 'green'
        else:
            color = 'blue'
        htmltext = f"<a href='https://www.zillow.com{house['hdpUrl']}' target='_blank'>House Link</a>" \
               f"<br/>" \
               f"Price {house['price']}<br/>" \
               f"Beds {house['bedrooms']} Bath {house['bathrooms']}<br/>" \
               f"Square ft {house['livingArea']}<br/>" \
               f"Days on Market {house['daysOnZillow']}<br/>" \
               f"Agent Name {house['attributionInfo']['agentName']}<br/>" \
               f"Agent Number {house['attributionInfo']['agentPhoneNumber']}<br/>" \
               f"Neighbour {house['neighborhoodRegion']['name']}<br/>"

        popup = folium.Popup(htmltext, max_width=300)

        icon = folium.Icon(color=color)

        folium.Marker(
            location=[house['latitude'], house['longitude']],
            popup=popup,
            icon =icon
        ).add_to(map)
    map_html = map._repr_html_()
    return map_html, filtered_houses