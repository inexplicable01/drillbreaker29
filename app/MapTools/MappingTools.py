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
        for bigcity in citywithneighbourhoods:
            if bigcity ==CityName:
                continue
            for feature in citygeojson_features[bigcity]:
                polygon = shape(feature['geometry'])
                if polygon.contains(point):
                    return feature['properties']['CityName'], feature['properties']['S_HOOD']
        for feature in WA_geojson_data['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return feature['properties']['CityName'], None
    else:
        for feature in WA_geojson_data['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                return feature['properties']['CityName'], None
        for bigcity in citywithneighbourhoods:
            for feature in citygeojson_features[bigcity]:
                polygon = shape(feature['geometry'])
                if polygon.contains(point):
                    return feature['properties']['CityName'], feature['properties']['S_HOOD']
    return None, None

def get_zone_as_array(brieflistinglist, washingtonzonescontroller):
    for brieflisting in brieflistinglist:
        brieflisting.outsideZones=True
    for bigcity in citywithneighbourhoods:
        for feature in citygeojson_features[bigcity]:
            polygon = shape(feature['geometry'])
            zone = washingtonzonescontroller.get_zone_id_by_name(feature['properties']['CityName'], feature['properties']['S_HOOD'])
            for brieflisting in brieflistinglist:
                point = Point(brieflisting.longitude, brieflisting.latitude)
                if polygon.contains(point):
                    brieflisting.zone_id = zone.id
                    brieflisting.outsideZones=False
                    print(zone)
                    print(brieflisting)
    for feature in WA_geojson_data['features']:
        polygon = shape(feature['geometry'])
        zone = washingtonzonescontroller.get_zone_id_by_name(feature['properties']['CityName'],
                                                             None)
        for brieflisting in brieflistinglist:
            point = Point(brieflisting.longitude, brieflisting.latitude)
            if polygon.contains(point):
                brieflisting.zone_id = zone.id
                brieflisting.outsideZones = False
                print(zone)
                print(brieflisting)






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

import copy
from branca.element import Template, MacroElement
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
# import imgkit

# WKHTMLTOIMAGE_PATH = os.getenv("WKHTMLTOIMAGE_PATH")
# imgkitconfig = imgkit.config(wkhtmltoimage=WKHTMLTOIMAGE_PATH)
def get_marker_color(list2penddays):
    # Replicates getMarkerColor()
    if list2penddays is None:
        return 'gray'
    elif list2penddays < 7:
        return 'green'
    elif list2penddays < 14:
        return 'orange'
    else:
        return 'red'
from pathlib import Path
def create_map(geojson_features, zonenames, map_html_path,map_image_path, soldhomes):
    # Create a base map
    m = folium.Map(location=[47.6815, -122.2087],
                   zoom_start=13)

    geojson_features_clone = copy.deepcopy(geojson_features)
    # Iterate through GeoJSON features and add them to the map
    bounds_points = []
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
        color = "purple"  # Default color
        label = "Unknown"
        matches_zone=False
        if "S_HOOD" in feature["properties"]:
            neighbourhood = feature["properties"]["S_HOOD"]
            if neighbourhood in zonenames:
                color = "orange"
                matches_zone = True
            label = neighbourhood
        elif "CityName" in feature["properties"]:
            city_name = feature["properties"]["CityName"]
            if city_name in zonenames:
                color = "orange"
                matches_zone = True
            label = city_name

        if matches_zone:
            if feature["geometry"]["type"] == "Polygon":
                for ring in polygon_coords:
                    for coord in ring:
                        if isinstance(coord[0], float) and isinstance(coord[1], float):
                            bounds_points.append([coord[1], coord[0]])  # lat, lon
            elif feature["geometry"]["type"] == "MultiPolygon":
                for polygon in polygon_coords:
                    for ring in polygon:
                        for coord in ring:
                            if isinstance(coord[0], float) and isinstance(coord[1], float):
                                bounds_points.append([coord[1], coord[0]])  # lat, lon

        if feature["geometry"]["type"] == "Polygon":
            location_for_folium = polygon_coords[0]
        elif feature["geometry"]["type"] == "MultiPolygon":
            location_for_folium = polygon_coords[0][0]

        pgGON = folium.Polygon(
            locations=location_for_folium,
            color=color,
            fill=True,
            fill_opacity=0.5,
            popup=folium.Popup(label, max_width=250)
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
        if matches_zone:
            styled_label = f"<div style='font-size:12px; font-weight:bold; opacity:0.50'>{label}</div>"
            pgGON.add_child(folium.Tooltip(styled_label, permanent=True))
        # else:
        #     styled_label = f"<div style='font-size:20px; font-weight:bold'>{label}</div>"
        pgGON.add_to(m)

    # marker_cluster = MarkerCluster().add_to(m)
    for listing in soldhomes:
        color = get_marker_color(listing.list2penddays)

        folium.Marker(
            location=[listing.latitude, listing.longitude],
            icon=folium.Icon(color=color, icon='home', prefix='fa')
        ).add_to(m)

    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed;
        bottom: 10px;
        left: 10px;
        width: 340px;
        height: 250px;
        z-index:9999;
        font-size:26px;
        background-color: white;
        border:2px solid gray;
        border-radius:8px;
        padding: 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    ">
    <b>Legend</b><br>
        <i style="background:red; width:12px; height:12px; display:inline-block; border-radius:50%; margin-right:6px;"></i> Pending in &lt; 7 days<br>
        <i style="background:orange; width:12px; height:12px; display:inline-block; border-radius:50%; margin-right:6px;"></i> Pending in 7–14 days<br>
        <i style="background:green; width:12px; height:12px; display:inline-block; border-radius:50%; margin-right:6px;"></i> Pending in 14-21 days<br>
        <i style="background:blue; width:12px; height:12px; display:inline-block; border-radius:50%; margin-right:6px;"></i> Pending in &gt; 21 days<br>
        <i style="background:gray; width:12px; height:12px; display:inline-block; border-radius:50%; margin-right:6px;"></i> Pending date unknown
    </div>
    {% endmacro %}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)
    if bounds_points:
        min_lat = min(pt[0] for pt in bounds_points)
        max_lat = max(pt[0] for pt in bounds_points)
        min_lon = min(pt[1] for pt in bounds_points)
        max_lon = max(pt[1] for pt in bounds_points)
        m.fit_bounds([[min_lon, min_lat], [max_lon, max_lat]])
    else:
        m = folium.Map(location=[47.6815, -122.2087], zoom_start=13)  # fallback
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
    driver.save_screenshot(map_image_path)

    # Close the browser session
    driver.quit()

    print(f"Map image saved at {map_image_path}")
    return map_html