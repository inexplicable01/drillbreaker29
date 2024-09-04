from flask import Blueprint, render_template,jsonify, redirect, url_for, request
from flask import Blueprint, redirect, url_for
# from app.RouteModel.EmailModel import sendEmailwithListingforclient
from app.ZillowAPI.ZillowDataProcessor import ZillowSearchForForSaleHomes,loadPropertyDataFromBrief
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.ZillowAPI.ZillowAPICall import *
from app.HeatMapProcessing import *
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import numpy as np
import random
hothomes_bp = Blueprint('hothomes_bp', __name__,url_prefix='/hothomes')
@hothomes_bp.route('/ballard', methods=['GET'])
def showHotHomes():
    neighbourhoods=['Fremont','Ballard','Wallingford']
    selectedhometypes=['SINGLE_FAMILY', 'TOWNHOUSE','CONDO' ]
    unfiltered_forsale=brieflistingcontroller.ForSaleListingsByNeighbourhoodsAndHomeTypes(neighbourhoods, selectedhometypes, 30, 'FOR_SALE')
    # for forsalehome in unfiltered_forsale:
    #     print(forsalehome)
    competivenessoption=['Not Very Competitive', 'to have a few Competing offers', 'Highly Competitive : Bidding War']
    infodump = []
    house_c=0
    for house in unfiltered_forsale:
        if house_c>5:
            break
        images=[]
        count = 0
        listingdetails = SearchZillowByZPID(house.zpid)
        if not listingdetails:
            continue
        try:
            if listingdetails['address']['city']!='Seattle':
                continue

            for photo in listingdetails['photos']:
                for jpeg in photo['mixedSources']['jpeg']:
                    if jpeg['width']==384:
                        images.append({
                            "url": jpeg['url'], "caption": photo['caption']
                        })
                        # count = count +1
                # if count>2:
                #     break
            estimatelistingdays = int(round(np.random.normal(7, 5)))
            estimatesoldprice = house.price+100000
            competitiveness =random.choice(competivenessoption)
            infodump.append(
                (listingdetails,house.zpid,images, house, estimatelistingdays,estimatesoldprice ,competitiveness)
            )
            house_c+=1

        except Exception as e:
            print(e)
    return render_template('HotHomes.html', infodump=infodump)

@hothomes_bp.route('/ballard', methods=['POST'])
def getUpdatedHomes():

    clientinterest={
        'area':['Fremont','Ballard','Wallingford'],
        'bedrooms_min':1,
        'bedrooms_max': 4,
        'bathrooms_min':1.5,
        'pricemax': 1700000
    }
    forsalebriefdata = ZillowSearchForForSaleHomes(clientinterest)

    for brieflisting in forsalebriefdata:

        try:
            propertydata = loadPropertyDataFromBrief(brieflisting)
            brieflisting.hdpUrl = propertydata['hdpUrl']
        except Exception as e:
            print(e, brieflisting)

    changebrieflistingarr,oldbrieflistingarr=brieflistingcontroller.SaveBriefListingArr(forsalebriefdata)

    return render_template('HotHomes.html')
# @openhouse_bp.route('/showopenhouseopportunity', methods=['GET','POST'])
# def SearchForOpenHouseRoute():
#     map_html = SearchForOpenHouses()
#     return render_template('OpenHouse.html', m=map_html)

# import matplotlib.pyplot as plt
# from io import BytesIO
# import base64

from app.MapTools.MappingTools import generateMap
@hothomes_bp.route('/forsale', methods=['GET'])
def forsalehomes():
    neighbourhoods=['Fremont','Ballard','Wallingford']
    selectedhometypes=['SINGLE_FAMILY', 'TOWNHOUSE','CONDO' ]
    unfiltered_forsale=brieflistingcontroller.ForSaleListingsByNeighbourhoodsAndHomeTypes(neighbourhoods, selectedhometypes, 30, 'FOR_SALE')

    return render_template('ForSale.html', m=generatethisMap(brieflistings=unfiltered_forsale,neighbourhoods=[],showneighbounds=False))

import folium
from shapely.geometry import shape, Point
import fiona

def generatethisMap(brieflistings, neighbourhoods, showneighbounds):
    if not brieflistings:
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
    zoom_start = 15 if max_diff < 0.01 else 13 if max_diff < 0.05 else 12 if max_diff < 0.1 else 10 if max_diff < 0.5 else 8
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)

    # click_js = """function onClick(e) {}"""

    custom_js = """
    function onClick(e) {
        console.log("Pin clicked with e:", e);
        console.log("Marker clicked, ZPID:", e.target.options.zpid);
        
        var event = new CustomEvent('pinClick', { detail: { zpid: e.target.options.zpid } });
        console.log("Dispatching event:", event);
    
            // Dispatch the event from the parent document
        window.parent.document.dispatchEvent(event);
    }
    """
    e = folium.Element(custom_js)
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
        marker = folium.Marker(
            location=[brieflisting.latitude, brieflisting.longitude],
            popup=popup,
            icon=icon,
            zpid=brieflisting.zpid
        )
        marker.add_to(m)

        custom_js = """
        function onMarkerClick(e) {
            var zpid = "2089376815";  // Replace with dynamic ZPID if available
            console.log("Marker clicked, ZPID:", zpid);
    
            // Create a custom event with the ZPID as detail
            var event = new CustomEvent('pinClick', { detail: { zpid: zpid } });
            console.log("Dispatching event:", event);
    
            // Dispatch the event from the parent document
            window.parent.document.dispatchEvent(event);
        }
    
        // Bind the onClick function to the marker
        document.querySelectorAll('.leaflet-marker-icon').forEach(function(marker) {
            marker.addEventListener('click', onMarkerClick);
        });
        """

        # Inject the custom JS into the map
        e = folium.Element(f'<script>{custom_js}</script>')
        m.get_root().html.add_child(e)



    # for brieflisting in brieflistings:
    #     list2penddays = brieflisting.list2penddays
    #     color = 'gray' if list2penddays is None else 'red' if list2penddays < 7 else 'orange' if 7 <= list2penddays < 14 else 'green' if 14 <= list2penddays < 21 else 'blue'
    #
    #     # Create marker
    #     icon = folium.Icon(color=color)
    #     popup_content = f"""
    #     <div>
    #         <strong>Neigh:</strong> {brieflisting.neighbourhood}<br/>
    #         <strong>Price:</strong> {brieflisting.price}<br/>
    #         <strong>Beds:</strong> {brieflisting.bedrooms} <strong>Baths:</strong> {brieflisting.bathrooms}<br/>
    #         <strong>ZPID:</strong> {brieflisting.zpid}<br/>
    #         <button onclick="updateInfoDiv('{brieflisting.zpid}')">Show ZPID</button>
    #     </div>
    #     """
    #     popup = folium.Popup(popup_content, max_width=300)
    #
    #     folium.Marker(
    #         location=[brieflisting.latitude, brieflisting.longitude],
    #         popup=popup,
    #         icon=icon
    #     ).add_to(m)
    #
    # # Inject custom JavaScript for updating the info-div
    #
    # m.get_root().html.add_child(folium.Element(custom_js))

    return m._repr_html_()

from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief
@hothomes_bp.route('/zpid/getdata', methods=['GET'])
def get_data():
    zpid = request.args.get('zpid')
    # Fetch data based on zpid

    brieflisting = brieflistingcontroller.get_listing_by_zpid(zpid)
    propertydata = loadPropertyDataFromBrief(brieflisting)
    if brieflisting is None:
        #get listing from rapid
        a =4
    else:
        b = 4
        data = {
            'neighborhood': 'Ballard',
            'price': brieflisting.price,
            'beds': 2,
            'baths': 2
        }
    images = []
    count = 0




    for photo in propertydata['photos']:
        for jpeg in photo['mixedSources']['jpeg']:
            if jpeg['width'] == 384:
                images.append({
                    "url": jpeg['url'], "caption": photo['caption']
                })
                # count = count +1
        # if count>2:
        #     break

    # Render the template with the data
    rendered_html = render_template('components/property_details.html',
                                    item=propertydata,
                                    images=images,
                                    brieflisting=brieflisting,
                                    estimatesoldprice=1000000,
                                    wayberbuyersavings=10500,
                                    estimatelistingdays=18,
                                    )

    # Return the rendered HTML as part of the JSON response
    return jsonify({'html': rendered_html})


@hothomes_bp.route('/mappotentialValue', methods=['GET', 'POST','PUT'])
def MapPotentialValue():
    # addresses = ["Address 1", "Address 2", "Address 3"]

    if request.method =='POST':
        days = 60
        description = request.form['description']
        # displayfun = request.form['displayfun']

        map_html2 = validateHomePredictionPrice2(description)
        return jsonify({'map_html2': map_html2, 'report': "Future Justification of Value"})
    elif request.method =='PUT':
        buildpotentiallowerlimit = request.form['buildpotentiallowerlimit']
        map_html, nu_hits = alladdresseswithbuilthomecalues(float(buildpotentiallowerlimit))
        return jsonify({'map_html': map_html, 'buildpotentiallowerlimit': buildpotentiallowerlimit, 'nu_hits':nu_hits})
    else:
        description = None
        buildpotentiallowerlimit=2000000
        averagenewbuildprice = None
        map_html2 = 'Display for Property details'
        # displayfun = SOLDHOTTNESS
    map_html, nu_hits = alladdresseswithbuilthomecalues(buildpotentiallowerlimit)

    return render_template('MapPotentialValue.html', map=map_html ,map2=map_html2,  description = description, buildpotentiallowerlimit=buildpotentiallowerlimit, nu_hits=nu_hits)