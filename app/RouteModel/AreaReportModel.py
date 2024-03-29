import folium
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    FindSoldHomesByLocation,\
    loadPropertyDataFromBrief,FindSoldHomesByNeighbourhood
import matplotlib.pyplot as plt

import base64
from io import BytesIO
from app.DBFunc.BriefListingController import brieflistingcontroller
import math
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# model = load('linear_regression_model.joblib')
def AreaReportGatherData(neighbourhoods):
    soldbrieflistingarr=[]
    count =0
    for neighbourhood in neighbourhoods:
        soldbrieflistingarr=  soldbrieflistingarr+ FindSoldHomesByNeighbourhood(neighbourhood,30)
    for brieflisting in soldbrieflistingarr:

        try:
            # if brieflisting.neighbourhood == 'North Delridge Seattle':
            #     print('pause')
            propertydata = loadPropertyDataFromBrief(brieflisting)
            listresults = ListingLengthbyBriefListing(propertydata)
            brieflisting.updateListingLength(listresults)
            brieflisting.hdpUrl = propertydata['hdpUrl']
        except Exception as e:
            print(e, brieflisting)


    brieflistingcontroller.SaveBriefListingArr(soldbrieflistingarr)


def ListAllNeighhourhoodsByCities(cities):
    return brieflistingcontroller.UniqueNeighbourhoodsByCities(cities)

def displayModel(neighbourhoods, selectedhometypes):
    unfiltered_soldhomes=brieflistingcontroller.ListingsByNeighbourhoodsAndHomeTypes(neighbourhoods, selectedhometypes, 30)
    df = pd.DataFrame([brieflisting.__dict__ for brieflisting in unfiltered_soldhomes])
    df = df.select_dtypes(include=['number'])
    print(df)
    features = df[['bathrooms', 'bedrooms', 'lotAreaValue','taxAssessedValue',]]  # Adjust based on your model
    target = df['price']
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    # Fit the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    living_area = X_test['taxAssessedValue']
    actual_prices = y_test
    predicted_prices = predictions
    errors = predicted_prices - actual_prices

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('Living Area (sqft)')
    ax1.set_ylabel('Actual Price', color=color)
    ax1.scatter(living_area, actual_prices, color=color, label='Actual Price', alpha=0.6)
    ax1.tick_params(axis='y', labelcolor=color)

    # Instantiate a second y-axis to plot the error
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Error ($)', color=color)  # we already handled the x-label with ax1
    ax2.scatter(living_area, errors, color=color, label='Error', alpha=0.6)
    ax2.tick_params(axis='y', labelcolor=color)

    # Show plot
    fig.tight_layout()  # To ensure there's no clipping of y-label
    plt.title('Actual Price vs. Living Area and Prediction Error')
    buf2 = BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)

    return base64.b64encode(buf2.read()).decode('utf-8')

def AreaReport(neighbourhoods, selectedhometypes):
    ## Calls zillow data Process
    ## Zillow Data Process puts listing in BriefListing Array
    housesoldpriceaverage = initiateSummarydata()
    unfiltered_soldhomes = []
    for neighbourhood in neighbourhoods:
        ## Gathering the Locations
        unfiltered_soldhomes = unfiltered_soldhomes + brieflistingcontroller.ListingsByNeighbourhood(neighbourhood, 30)
    ## Gets List of briefhomedataraw


    soldhomes=[]
    for brieflisting in unfiltered_soldhomes:
        if brieflisting.homeType not in selectedhometypes:
            continue
        soldhomes.append(brieflisting)

    for brieflisting in soldhomes:
        try:
            bedbathcode = int(brieflisting.bedrooms)+float(brieflisting.bathrooms)*100
            if 101<=bedbathcode<=102:
                housesoldpriceaverage["1bed1bath"]["count"] +=1
                housesoldpriceaverage["1bed1bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["1bed1bath"]["houses"].append(brieflisting)
            elif 201.5<=bedbathcode<=202.5:
                housesoldpriceaverage["2bed2bath"]["count"] +=1
                housesoldpriceaverage["2bed2bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["2bed2bath"]["houses"].append(brieflisting)
            elif 302 <= bedbathcode <= 302.5:
                housesoldpriceaverage["3bed2bath"]["count"] +=1
                housesoldpriceaverage["3bed2bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["3bed2bath"]["houses"].append(brieflisting)
            elif 302.5 < bedbathcode <= 304:
                housesoldpriceaverage["3bed3bath"]["count"] +=1
                housesoldpriceaverage["3bed3bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["3bed3bath"]["houses"].append(brieflisting)
            elif 400 <= bedbathcode <= 402:
                housesoldpriceaverage["4bed2-bath"]["count"] +=1
                housesoldpriceaverage["4bed2-bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["4bed2-bath"]["houses"].append(brieflisting)
            elif 402 < bedbathcode <= 404:
                housesoldpriceaverage["4bed3+bath"]["count"] +=1
                housesoldpriceaverage["4bed3+bath"]["totalprice"] += brieflisting.price
                housesoldpriceaverage["4bed3+bath"]["houses"].append(brieflisting)

        except Exception as e:
            print('Error with ', brieflisting)
    # Create a map centered around Ballard, Seattle

    for key, value in housesoldpriceaverage.items():
        value['minprice']=1000000000
        value['maxprice']=0
        if value['count']==0:
            value['aveprice'] = 'NA'
        else:
            value['aveprice']= int(value['totalprice']/value['count'])
        for brieflisting in value["houses"]:
            if brieflisting.price<value['minprice']:
                value['minprice'] = brieflisting.price
            if brieflisting.price>value['maxprice']:
                value['maxprice'] = brieflisting.price
    pricedelta=[]
    days_to_pending=[]

    plt.figure()
    colors = ['blue', 'red',  'purple']  # Example colors for 1-5 bedrooms
    for brieflisting in soldhomes:
        # print('home_type',brieflisting.homeType)
        if brieflisting.pricedelta is not None and brieflisting.list2penddays is not None:
            if brieflisting.list2penddays > 300:
                continue
            days_to_pending.append(brieflisting.list2penddays)
            # bedrooms.append(round(brieflisting.bedrooms))
            if brieflisting.bedrooms is None:
                continue
            if round(brieflisting.bedrooms) > 3:
                color = 'orange'
            else:
                color = colors[round(brieflisting.bedrooms)-1]
            if (brieflisting.price-brieflisting.listprice)>600000.0:
                print(brieflisting)
                continue

            # Use price to determine the size of the marker
            size = (brieflisting.price / 3000000.0) * 30 +24
            if size > 174:
                size = 174
            plt.scatter(brieflisting.list2penddays, brieflisting.price-brieflisting.listprice, c=color, s=size)
    # Creating the plot

    plt.title('Price Change vs. Days to Pending')
    plt.xlabel('Days to Pending')
    plt.ylabel('Price Change')
    for i, color in enumerate(colors):
        plt.scatter([], [], c=color, label=f'{i + 1} Bedrooms')
    plt.scatter([], [], c='orange', label='>4 Bedrooms')
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='Bedroom Count')

    # Saving the plot to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    plot_url = base64.b64encode(buf.read()).decode('utf-8')


    plt.figure()
    colors = ['blue', 'red',  'purple']  # Example colors for 1-5 bedrooms
    for brieflisting in soldhomes:
        # print('home_type',brieflisting.homeType)
        if brieflisting.pricedelta is not None and brieflisting.list2penddays is not None:
            if brieflisting.list2penddays > 300:
                continue
            days_to_pending.append(brieflisting.list2penddays)
            # bedrooms.append(round(brieflisting.bedrooms))
            if brieflisting.bedrooms is None:
                continue
            if round(brieflisting.bedrooms) > 3:
                color = 'orange'
            else:
                color = colors[round(brieflisting.bedrooms)-1]
            if abs(brieflisting.price-brieflisting.listprice)>600000.0:
                print(brieflisting)
                continue

            # Use price to determine the size of the marker
            size = (brieflisting.price / 3000000.0) * 30 +24
            if size > 174:
                size = 174
            plt.scatter(brieflisting.list2penddays, brieflisting.price, c=color, s=size)
    # Creating the plot

    plt.title('Price  vs. Days to Pending')
    plt.xlabel('Days to Pending')
    plt.ylabel('Price')
    for i, color in enumerate(colors):
        plt.scatter([], [], c=color, label=f'{i + 1} Bedrooms')
    plt.scatter([], [], c='orange', label='>4 Bedrooms')
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='Bedroom Count')

    # Saving the plot to a bytes buffer
    buf2 = BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)

    plot_url2 = base64.b64encode(buf2.read()).decode('utf-8')

    return generateMap(soldhomes, neighbourhoods), soldhomes,housesoldpriceaverage, plot_url, plot_url2



from app.MapTools.SeattleNeighCoord import *
def generateMap(soldhomes, neighbourhoods):
    m = folium.Map(location=[47.6762, -122.3860], zoom_start=13)

    # Create a polygon over Ballard and add it to the map
    folium.Polygon(locations=ballard_coordinates, color='blue', fill=True, fill_color='blue').add_to(m)
    # Create a polygon over Ballard and add it to the map
    folium.Polygon(locations=fremont_coordinates, color='green', fill=True, fill_color='green').add_to(m)
    # Create a polygon over Ballard and add it to the map
    folium.Polygon(locations=wallingford_coordinates, color='green', fill=True, fill_color='green').add_to(m)
    # map = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    click_js = """function onClick(e) {}"""
    e = folium.Element(click_js)
    html = m.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e
    for brieflisting in soldhomes:
        list2penddays = brieflisting.list2penddays
        if list2penddays is None:
            color = 'gray'
            list2penddays=999
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
                       f"$Change {brieflisting.price-brieflisting.listprice}<br/>" \
                       f"Beds {brieflisting.bedrooms} Bath {brieflisting.bathrooms}<br/>" \
                   f"Square ft {brieflisting.livingArea}<br/>" \
                   f"List to Contract {list2penddays}<br/>"
        except Exception as e:
            htmltext=''

        # f"<a href='https://www.zillow.com{house['hdpUrl']}' target='_blank'>House Link</a>" \
        # f"<br/>" \
        popup = folium.Popup(htmltext, max_width=300)

        icon = folium.Icon(color=color)

        folium.Marker(
            location=[brieflisting.latitude, brieflisting.longitude],
            popup=popup,
            icon =icon
        ).add_to(m)

    map_html = m._repr_html_()
    return map_html

# def ListingLength(soldhouse, Listing, db):
#
#     if soldhouse.list2pendCheck==0

def initiateSummarydata():
    return{
        "1bed1bath": {
            "beds": 1,
            "baths": 1,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "2bed2bath": {
            "beds": 2,
            "baths": 2,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "3bed2bath": {
            "beds": 3,
            "baths": 2,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "3bed3bath": {
            "beds": 3,
            "baths": 3,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "4bed2-bath": {
            "beds": 4,
            "baths": 2,
            "count": 0,
            "totalprice": 0,
            "houses": []
        },
        "4bed3+bath": {
            "beds": 4,
            "baths": 3,
            "count": 0,
            "totalprice": 0,
            "houses": []
        }
    }