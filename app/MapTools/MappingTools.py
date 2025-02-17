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
file_path = 'app/MapTools/Neighborhood_Seattle.geojson'
with open(file_path, 'r') as f:
    Neighborhood_Seattle_geojson_data = json.load(f)
file_path = 'app/MapTools/kirkland_neighborhoods.geojson'
with open(file_path, 'r') as f:
    kirkland_neighborhoods_geojson_data = json.load(f)
file_path = 'app/MapTools/shoreline_neighborhoods.geojson'
with open(file_path, 'r') as f:
    shoreline_geojson_data = json.load(f)
file_path = 'app/MapTools/Bellevue_neighbourhoods.geojson'
with open(file_path, 'r') as f:
    bellevue_geojson_data = json.load(f)

file_path = 'app/MapTools/redmond_neighborhoods.geojson'
with open(file_path, 'r') as f:
    redmond_geojson_data = json.load(f)

# file_path = 'app/MapTools/renton_neighborhoods.geojson'
# with open(file_path, 'r') as f:
#     renton_geojson_data = json.load(f)

WA_geojson_features = (WA_geojson_data['features']+kirkland_neighborhoods_geojson_data['features']+
                       shoreline_geojson_data['features']+ bellevue_geojson_data['features']
                       +redmond_geojson_data['features'] + Neighborhood_Seattle_geojson_data['features'])
citygeojson_features = {'Seattle':Neighborhood_Seattle_geojson_data['features'],
                        'Kirkland':kirkland_neighborhoods_geojson_data['features'],
                        'Redmond':redmond_geojson_data['features'],
                        'Bellevue':bellevue_geojson_data['features'],
                        'Shoreline':shoreline_geojson_data['features']}

featureAreas= {}
for feature in WA_geojson_data['features']:
    if feature['properties']:
        if 'CityName' in feature['properties'].keys() and 'S_HOOD' not in feature['properties'].keys():
            featureAreas[feature['properties']['CityName']] = []

for feature in WA_geojson_features:
    if feature['properties']:
        if 'CityName' in feature['properties'].keys() and 'S_HOOD' in feature['properties'].keys():
            if feature['properties']['CityName'] not in featureAreas.keys():
                featureAreas[feature['properties']['CityName']] = []
            else:
                featureAreas[feature['properties']['CityName']].append(feature['properties']['S_HOOD'])


citywithneighbourhoods=['Seattle','Kirkland','Redmond','Bellevue','Shoreline']
def get_zone(lat, lon, CityName):
    point = Point(lon, lat)
    if CityName in citywithneighbourhoods:
        for feature in citygeojson_features[CityName]:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return feature['properties']['CityName'], feature['properties']['S_HOOD']
    else:
        for feature in WA_geojson_data['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return feature['properties']['CityName'], None
    return None, None



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

from folium import GeoJson
import copy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

def create_map(geojson_features, neighbourhoods_subs, cities, map_html_path,map_image_path):
    # Create a base map
    m = folium.Map(location=[47.6791, -122.3270], zoom_start=13)

    geojson_features_clone = copy.deepcopy(geojson_features)
    # Iterate through GeoJSON features and add them to the map
    for feature in geojson_features_clone:
        if feature["geometry"]["type"] == "Polygon":
            # Adjust coordinates for Leaflet format
            polygon_coords= [
                [[coord[1], coord[0]] for coord in ring]  # Swap x, y
                for ring in feature["geometry"]["coordinates"]
            ]
        elif feature["geometry"]["type"] == "MultiPolygon":
            polygon_coords= [
                [
                    [[coord[1], coord[0]] for coord in ring]  # Swap x, y
                    for ring in polygon
                ]
                for polygon in feature["geometry"]["coordinates"]
            ]

        # Determine color based on cities or neighbourhoods
        color = "gray"  # Default color
        label = "Unknown"
        if "CityName" in feature["properties"]:
            city_name = feature["properties"]["CityName"]
            color = "orange" if city_name in cities else "purple"
            label = city_name
        elif "S_HOOD" in feature["properties"]:
            neighbourhood = feature["properties"]["S_HOOD"]
            color = "orange" if neighbourhood in neighbourhoods_subs else "purple"
            label = neighbourhood

        # Add a polygon to the map
        # poly = GeoJson(
        #     feature,
        #     style_function=lambda x, color=color: {
        #         "fillColor": color,
        #         "color": color,
        #         "weight": 2,
        #         "fillOpacity": 0.5
        #     }
        # )

        pgGON = folium.Polygon(
            locations=polygon_coords[0],
            # Reverse coordinates (longitude, latitude -> latitude, longitude)
            color=color,
            fill=True,
            fill_opacity=0.5,
            popup = folium.Popup(label)
        )

        # Create a polygon object
        # polygon = shapely.geometry.Polygon(polygon_coords[0])
        #
        # # Calculate the centroid of the polygon
        # centroid = polygon.centroid
        # folium.Marker(
        #     location=[centroid.y, centroid.x],
        #     popup=label
        # ).add_to(m)

        # poly.add_child(folium.Tooltip(label))
        # poly.add_to(m)

        pgGON.add_child(folium.Tooltip(label, permanent=True))

        # Add the polygon to the map
        pgGON.add_to(m)

    # Save the map as an HTML file
    map_html = m._repr_html_()

    m.save(map_html_path)  # Save the map as an HTML file
    # Configure Selenium to run headless
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    # Open the saved HTML map
    driver.get("file://" + os.path.abspath(map_html_path))

    # Wait to ensure map is fully loaded
    time.sleep(2)

    # Save screenshot of the map
    # image_path = f"static/map.png"
    driver.save_screenshot(map_image_path)

    # Close the browser session
    driver.quit()

    print(f"Map image saved at {map_image_path}")
    return map_html