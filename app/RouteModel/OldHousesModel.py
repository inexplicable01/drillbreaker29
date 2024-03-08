import folium
from app.DataBaseFunc import dbmethods
from joblib import load

model = load('linear_regression_model.joblib')
from folium.plugins import HeatMap


def WhereOldBuild(selected_address=None):
    CheapHomeValue = 500000
    coords=[]
    lat=0
    long=0
    addresses = dbmethods.AddressesBuiltYearsAgo(20)
    addressestoclick=[]
    for address in addresses:
        if address.zestimate_value<CheapHomeValue:
            addressestoclick.append(address.addr_full)
            coords.append([address.latitude, address.longitude])
            lat = lat + address.latitude
            long = long + address.longitude
            print('old' + address.addr_full, 'Bed',address.bedrooms,'Bath',address.bathrooms,
                  'Size',address.living_area, 'Price',address.zestimate_value)


    if len(coords)==0:
        m = folium.Map(location=[47.608013, -122.335167], zoom_start=13)
        HeatMap(coords).add_to(m)
        m = m._repr_html_()
        return m
    lat = lat/len(coords)
    long = long / len(coords)

    # Add markers with popups to the map
    # for address in addresses:
    if selected_address is None:
        address = addresses[0]
    else:
        for i_address in addresses:
            if i_address.addr_full==selected_address:
                address = i_address
    m = folium.Map(location=(address.latitude, address.longitude), zoom_start=13)

    # Add the heat map layer to the map
    HeatMap(coords).add_to(m)


    folium.Marker(
        location=[address.latitude, address.longitude],
        popup=folium.Popup(address.detailStr(), parse_html=True),
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    averagenewbuildprice, averagepriceitems = dbmethods.find_Average_New_Build_Prices(address)
    for item in averagepriceitems:
        closeaddress = item['address']
        folium.Marker(
            location=[closeaddress.latitude, closeaddress.longitude],
            popup=folium.Popup(closeaddress.detailStr() + str(item['distance']), parse_html=True),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    # displaystring = closeaddress[0].addr_full + closeaddress[1].addr_full


    m = m._repr_html_()
    return m, addressestoclick, averagenewbuildprice


