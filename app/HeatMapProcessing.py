import folium
from folium.plugins import HeatMap

from datetime import timedelta
from jinja2 import Template
from folium.map import Marker
import matplotlib.colors as mcolors
import matplotlib.cm as cm

# from app.DataBaseFunc import dbmethods
from joblib import load
import datetime
SOLDHOTTNESS = 'SOLDHOTTNESS'
EXPENSIVEHOME =  'EXPENSIVEHOME'
min_price=1000000
max_price=5000000

model = load('linear_regression_model.joblib')
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


def get_color(price, min_price, max_price):
    # Normalize the price to a value between 0 and 1
    normalized_price = (price - min_price) / (max_price - min_price)

    # Use Matplotlib to get a color from a colormap
    color = cm.jet(normalized_price)  # 'jet' is an example of a colormap

    # Convert RGBA color to a hex format
    return mcolors.to_hex(color)
def HeatMapGen(days, displayfun):
    current_date = datetime.now()
    days_ago = current_date - timedelta(days=days)
    coords=[]
    lat=0
    long=0
    listings = dbmethods.AllListingsforHeatmap()
    if displayfun==SOLDHOTTNESS:
        for listing in listings:
            try:
                if listing is None:
                    continue
                if listing.soldtime is None:
                    continue
            except Exception:
                print('sdf')
            if days_ago <= listing.soldtime <= current_date:
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
    listings = dbmethods.AllListingsforHeatmap()
    for listing in listings:
        if listing is None:
            continue
        if listing.dateSold is None:
            continue
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

def WhereNewBuild():

    coords=[]
    lat=0
    long=0
    addresses = dbmethods.AddressesBuiltWithinLast4years()
    for address in addresses:
        if address.zestimate_value>0:
            coords.append([address.latitude, address.longitude])
            lat = lat + address.latitude
            long = long + address.longitude
            # print('new' + address.addr_full, 'Bed',address.bedrooms,'Bath',address.bathrooms,
            #       'Size',address.living_area, 'Price',address.zestimate_value)
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



def createblankseattlemap():
    m = folium.Map(location=[47.608013, -122.335167], zoom_start=13)
    m = m._repr_html_()
    return m

def createblankNewyorkmap():
    m = folium.Map(location=[40.608013, -74], zoom_start=13)
    m = m._repr_html_()
    return m

click_template = """{% macro script(this, kwargs) %}
    var {{ this.get_name() }} = L.marker(
        {{ this.location|tojson }},
        {{ this.options|tojson }}
    ).addTo({{ this._parent.get_name() }}).on('click', onClick);
{% endmacro %}"""
Marker._template = Template(click_template)
def alladdresseswithbuilthomecalues(value_increase=1000000):
    addresses = dbmethods.AddressesBuiltYearsAgo(15)

    entries_to_update = []
    ## update every 200
    coords = []
    lat = 0
    long = 0
    h = 0
    markers_info = []
    build_cost=1500000
    hackcheck=[]
    addressestoclick = []
    for address in addresses:
        new = True
        print("\n")
        print(address.detailStr())
        if address.newbuild_prediction is None:
            hackcheck.append(address)
            averagenewbuildprice, averagepriceitems = dbmethods.find_Average_New_Build_Prices(address, 0.5)
            # print(averagenewbuildprice)
            entries_to_update.append({
                'id': address.id,  # assuming there's an 'id' primary key
                'newbuild_prediction': averagenewbuildprice,
            })

            new=True
            address.newbuild_prediction = averagenewbuildprice
        if (address.newbuild_prediction-address.zestimate_value - build_cost)>value_increase:
            buildvalue = address.newbuild_prediction-address.zestimate_value- build_cost
            if new:
                addressestoclick.append(address)
                pin_color = get_color(buildvalue, 1000000, 3000000)
                icon = folium.Icon(color='white', icon_color=pin_color,  icon='home')
                markers_info.append(([address.latitude, address.longitude],
                                     f"{address.price_vs_prediction_printout()}",
                                     icon))
                coords.append([address.latitude, address.longitude])
                lat = lat + address.latitude
                long = long + address.longitude
                print('VALUE! ' + address.price_vs_prediction_printout())
                print(h)
                h = h+ 1
        if len(entries_to_update)>10:
            dbmethods.UpdateDB(entries_to_update)
            entries_to_update=[]
        # if h>20:
        #     break
    if len(entries_to_update)>0:
        dbmethods.UpdateDB(entries_to_update)
        entries_to_update = []
    if len(coords) == 0:
        return createblankseattlemap()
    lat = lat/len(coords)
    long = long / len(coords)



    location_center = [lat, long]
    m = folium.Map(location_center, zoom_start=13)


    click_js = """function onClick(e) {
                     var popupContent = e.target.getPopup().getContent();
                     var customString = popupContent.innerText || popupContent.textContent;
                     window.parent.document.getElementById('description').innerText = customString;
                   }"""
    e = folium.Element(click_js)
    html = m.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e

    # Add marker (click on map an alert will display with latlng values)

    for coords, description,icon in markers_info:

        marker = folium.Marker(
            location=coords,
            popup=folium.Popup(description),  # The popup will contain the custom string
            icon=icon
        )
        marker.add_to(m)
    map_html= m._repr_html_()
    # m = folium_map._repr_html_()
    return map_html, len(markers_info)

def validateHomePredictionPrice(description):
    return createblankseattlemap()

def validateHomePredictionPrice2(description):
    parts = [part.strip() for part in description.split(',')]

    # Extract each part by its position
    addr_full = parts[0]
    address = dbmethods.find_addresses_based_on_Addr_full(addr_full)
    averagenewbuildprice, averagepriceitems = dbmethods.find_Average_New_Build_Prices(address, 0.5)
    location_center = [address.latitude, address.longitude]
    m = folium.Map(location_center, zoom_start=13)
    folium.Marker(
        location=location_center,
        popup=folium.Popup(address.detailStr()),  # The popup will contain the custom string
        tooltip='Click me!',
        icon = folium.Icon(color='red')
    ).add_to(m)
    for item in averagepriceitems:
        closeaddress = item['address']
        try:
            pin_color = get_color(address.zestimate_value, min_price, max_price)
            icon = folium.Icon(color='white', icon_color=pin_color,  icon='home')

            folium.Marker(
                location=[closeaddress.latitude, closeaddress.longitude],
                popup=folium.Popup(closeaddress.detailStr(), parse_html=True),
                icon=icon
            ).add_to(m)
            print([closeaddress.latitude, closeaddress.longitude])
        except Exception as e:
            print(e)
            continue

    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = m.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    map_html = m._repr_html_()
    return map_html


    # click_js = """function onClick(e) {
    #                  var point = e.latlng; alert(point)
    #                  }"""
    #
    # click_js = """function onClick(e) {
    #                  var point = e.latlng;
    #                  window.parent.document.getElementById('latlon').innerText = 'Lat: ' + point.lat.toFixed(5) + ', Lon: ' + point.lng.toFixed(5);
    #                }"""
    #
    # click_js = """function onClick(e) {
    #                  var customString = e.target.getPopup().getContent();
    #                  window.parent.document.getElementById('label').innerText = customString;
    #                }"""
def highvalueMap(value_increase=1000000):
    addresses = dbmethods.AddressesBuiltYearsAgo(15)

    entries_to_update = []
    ## update every 200
    coords = []
    lat = 0
    long = 0
    h = 0
    markers_info = []
    build_cost=1500000
    hackcheck=[]
    addressestoclick = []
    for address in addresses:
        print("\n")
        print(address.detailStr())
        if (address.newbuild_prediction-address.zestimate_value - build_cost)>value_increase:
            buildvalue = address.newbuild_prediction-address.zestimate_value- build_cost
            addressestoclick.append(address)
            pin_color = get_color(buildvalue, 1000000, 3000000)
            icon = folium.Icon(color='white', icon_color=pin_color,  icon='home')
            markers_info.append(([address.latitude, address.longitude, buildvalue],
                                 f"{address.price_vs_prediction_printout()}",
                                 icon))
            coords.append([address.latitude, address.longitude])
            lat = lat + address.latitude
            long = long + address.longitude
            print('VALUE! ' + address.price_vs_prediction_printout())
            print(h)

    if len(coords)==0:
        m = folium.Map(location=[47.608013, -122.335167], zoom_start=13)
        HeatMap(coords).add_to(m)
        m = m._repr_html_()
        return m
    lat = lat/len(coords)
    long = long / len(coords)
    m = folium.Map(location=[lat, long], zoom_start=13)

    # Add the heat map layer to the map
    HeatMap(coords, max_val=max(buildvalue for *_, buildvalue in coords)).add_to(m)
    m = m._repr_html_()
    return m


def WaterFrontProperties():
    waterfrontprops = dbmethods.WaterFrontProps()
    coords = []
    lat = 0
    long = 0
    count = 0
    markers_info = []
    build_cost=1500000
    hackcheck=[]
    addressestoclick = []
    for address in waterfrontprops:
        # print("\n")
        # print(address.detailStr())

        addressestoclick.append(address)

        icon = folium.Icon(color='white',  icon='home')
        markers_info.append(([address.latitude, address.longitude],
                             f"{address.addr_full}",
                             icon))
        coords.append([address.latitude, address.longitude])
        lat = lat + address.latitude
        long = long + address.longitude
        count = count +1
        if count>1000:
            break

    if len(coords) == 0:
        return createblankseattlemap()
    lat = lat/len(coords)
    long = long / len(coords)
    m = folium.Map(location=[lat, long], zoom_start=13)

    # Add the heat map layer to the map
    HeatMap(coords).add_to(m)
    m = m._repr_html_()
    return m

def PredictionError():
    newbuilds = dbmethods.PropertiesBuiltAfter()
    coords = []
    lat = 0
    long = 0
    markers_info = []
    y_pred = model.predict(newbuilds)
    for index, row  in newbuilds.iterrows():
        # print("\n")
        # print(address.detailStr())
        error= row['zestimate_value'] - y_pred[index]
        # addressestoclick.append(address)
        pin_color = get_color(error, 0, 3000000)
        icon = folium.Icon(color=pin_color, icon_color=pin_color, icon='home')
        # icon = folium.Icon(color='white',  icon='home')
        markers_info.append(([row['latitude'], row['longitude']],
                             f"zest {round(row['zestimate_value'])}\npred  {round(y_pred[index])}\nerror {round(error)} ",
                             icon))
        coords.append([row['latitude'], row['longitude']])
        lat = lat + row['latitude']
        long = long + row['longitude']
        # count = count +1
        # if count>1000:
        #     break

    if len(coords) == 0:
        return createblankseattlemap()
    lat = lat/len(coords)
    long = long / len(coords)
    m = folium.Map(location=[lat, long], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = m.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    for coord, description,icon in markers_info:

        # marker = folium.Marker(
        #     location=coord,
        #     # popup=folium.Popup(description),  # The popup will contain the custom string
        #     # icon=icon
        # )
        # marker.add_to(m)
        folium.Marker(
            location=coord,
            popup=folium.Popup(description),
            icon=icon
        ).add_to(m)
    # Add the heat map layer to the map
    # HeatMap(coords).add_to(m)
    # for coord in coords:
    #     folium.Marker(
    #         location=coord,
    #         # popup=folium.Popup(closeaddress.detailStr(), parse_html=True),
    #         # icon=icon
    #     ).add_to(m)

    m = m._repr_html_()
    return m
