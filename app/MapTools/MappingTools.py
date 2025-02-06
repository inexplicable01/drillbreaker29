import folium
from shapely.geometry import shape, Point
import fiona
import json

def load_geojson(geojson_path):
    with fiona.open(geojson_path, 'r') as src:
        features = [feature for feature in src]
    return features


file_path = 'app/MapTools/Neighborhood_Map_Atlas_Neighborhoods.geojson'
with open(file_path, 'r') as f:
    geojson_data = json.load(f)
geojson_features = geojson_data['features']


def replace_none(obj):
    if isinstance(obj, list):
        return [replace_none(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: replace_none(v) for k, v in obj.items()}
    elif obj is None:
        return None  # Explicitly returning None to align with JSON `null`
    return obj


geojson_features = replace_none(geojson_data['features'])

file_path = 'app/MapTools/WSDOT_-_City_Limits.geojson'
with open(file_path, 'r') as f:
    WA_geojson_data = json.load(f)
WA_geojson_features = WA_geojson_data['features']

WA_geojson_features = replace_none(WA_geojson_data['features'])



def get_neighborhood_in_Seattle(lat, lon):
    point = Point(lon, lat)
    for feature in geojson_features:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return [feature['properties']['L_HOOD'], feature['properties']['S_HOOD'] ]# Using 'L_HOOD' for neighborhood name
    return [None, None]

def get_neighborhood_List_in_Seattle():
    l =[]
    for feature in geojson_features:
        l.append([feature['properties']['L_HOOD'], feature['properties']['S_HOOD'] ])# Using 'L_HOOD' for neighborhood name
    return l

def findNeighbourhoodfromCoord(city,xcoord,ycoord):
    # get_neighborhood(sample_lat,sample_lon)
    [neighbourhood, neighbourhood_sub] =get_neighborhood_in_Seattle(ycoord, xcoord)
    cities2Neigh = {

        'Shoreline': 'Shoreline',
        'Seattle': neighbourhood,
        'Bothell': 'Bothell',
        'Kenmore': 'Kenmore',
        'Kirkland': 'Kirkland',
        'Woodinville': 'Woodinville',
        'Redmond': 'Redmond',
        'Duvall': 'Duvall',
        'Carnation': 'Carnation',
        'Auburn': 'Auburn',
        'Bellevue': 'Bellevue',
        'Black Diamond': 'Black Diamond',
        'Burien': 'Burien',
        'Clyde Hill': 'Clyde Hill',
        'Covington': 'Covington',
        'Des Moines': 'Des Moines',
        'Enumclaw': 'Enumclaw',
        'Federal Way': 'Federal Way',
        'Hunts Point': 'Hunts Point',
        'Issaquah': 'Issaquah',
        'Kenmore': 'Kenmore',
        'Kent': 'Kent',
        'Lake Forest Park': 'Lake Forest Park',
        'Maple Valley': 'Maple Valley',
        'Medina': 'Medina',
        'Mercer Island': 'Mercer Island',
        'Milton': 'Milton',
        'Newcastle': 'Newcastle',
        'Normandy Park': 'Normandy Park',
        'North Bend': 'North Bend',
        'Pacific': 'Pacific',
        'Renton': 'Renton',
        'Sammamish': 'Sammamish',
        'SeaTac': 'SeaTac',
        'Skykomish': 'Skykomish',
        'Snoqualmie': 'Snoqualmie',
        'Tukwila': 'Tukwila',
        'Yarrow Point': 'Yarrow Point'
    }

    if city in cities2Neigh.keys():
        return cities2Neigh[city]
    else:
        return 'FIXME'


def generateMap(brieflistings, neighbourhoods,showneighbounds):
    if not brieflistings:
        # Return a default map if no homes are provided
        return folium.Map(location=[47.6762, -122.3860], zoom_start=13)

    # Calculate bounds
    min_lat = min(home.latitude for home in brieflistings)
    max_lat = max(home.latitude for home in brieflistings)
    min_lon = min(home.longitude for home in brieflistings)
    max_lon = max(home.longitude for home in brieflistings)

    # Calculate center of the map
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    # Calculate the maximum distance (in degrees) which could be used to adjust zoom
    max_diff = max(max_lat - min_lat, max_lon - min_lon)

    # Simple heuristic to determine zoom level based on max difference
    if max_diff < 0.01:
        zoom_start = 15
    elif max_diff < 0.05:
        zoom_start = 13
    elif max_diff < 0.1:
        zoom_start = 12
    elif max_diff < 0.5:
        zoom_start = 10
    else:
        zoom_start = 8
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

    if showneighbounds:
        print('setupneighbounds')
        # folium.Polygon(locations=ballard_coordinates, color='blue', fill=True, fill_color='blue').add_to(m)
        # # Create a polygon over Ballard and add it to the map
        # folium.Polygon(locations=fremont_coordinates, color='green', fill=True, fill_color='green').add_to(m)
        # # Create a polygon over Ballard and add it to the map
        # folium.Polygon(locations=wallingford_coordinates, color='yellow', fill=True, fill_color='green').add_to(m)

    # Create a polygon over Ballard and add it to the map
    # folium.Polygon(locations=ballard_coordinates, color='blue', fill=True, fill_color='blue').add_to(m)
    # # Create a polygon over Ballard and add it to the map
    # folium.Polygon(locations=fremont_coordinates, color='green', fill=True, fill_color='green').add_to(m)
    # # Create a polygon over Ballard and add it to the map
    # folium.Polygon(locations=wallingford_coordinates, color='yellow', fill=True, fill_color='green').add_to(m)
    # # map = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = m.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    coordave=[0,0]
    for brieflisting in brieflistings:
        list2penddays = brieflisting.list2penddays
        if list2penddays is None:
            color = 'gray'
            list2penddays = 999
            brieflisting.listprice = 999999
        else:
            if list2penddays < 7:
                color = 'red'
            elif 7 <= list2penddays < 14:
                color = 'orange'
            elif 14 <= list2penddays < 21:
                color = 'green'
            else:
                color = 'blue'
        try:
            htmltext = f"<a href='https://www.zillow.com{brieflisting.hdpUrl}' target='_blank'>House Link</a><br/>" \
                       f"Neigh {brieflisting.neighbourhood}<br/>" \
                       f"Sold Price {brieflisting.price}<br/>" \
                       f"$Change {brieflisting.price - brieflisting.listprice}<br/>" \
                       f"Beds {brieflisting.bedrooms} Bath {brieflisting.bathrooms}<br/>" \
                       f"lat {brieflisting.latitude} long {brieflisting.longitude}<br/>" \
                       f"Square ft {brieflisting.livingArea}<br/>" \
                       f"List to Contract {list2penddays}<br/>"
        except Exception as e:
            htmltext = ''

        # f"<a href='https://www.zillow.com{house['hdpUrl']}' target='_blank'>House Link</a>" \
        # f"<br/>" \
        popup = folium.Popup(htmltext, max_width=300)

        icon = folium.Icon(color=color)
        folium.Marker(
            location=[brieflisting.latitude, brieflisting.longitude],
            popup=popup,
            icon=icon
        ).add_to(m)

    map_html = m._repr_html_()
    return map_html