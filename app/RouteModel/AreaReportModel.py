# from numpy import int256

from app.MapTools.MappingTools import generateMap

import matplotlib.pyplot as plt

import base64
from io import BytesIO
from app.DBFunc.BriefListingController import brieflistingcontroller
import pandas as pd
from app.GraphTools.plt_plots import *
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.config import RECENTLYSOLD, FOR_SALE


# model = load('linear_regression_model.joblib')
def AreaReportGatherData(neighbourhoods, doz):
    # soldbriefarr=[]
    # forsalebriefarr=[]
    count =0



def ListAllNeighhourhoodsByCities(neighbourhoods, doz):
    return brieflistingcontroller.ListingsByCities(neighbourhoods, doz)





from datetime import datetime, timedelta
def AreaReportModelRun(selected_zones, selectedhometypes,soldlastdays):
    unfiltered_homes = []
    zone_ids=[]
    for zonename in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zonename)
        if wzone:
            zone_ids.append(wzone.id)
            # unfiltered_homes=unfiltered_homes+wzone.brief_listings
            # for brieflisting in wzone.brief_listings:
            #     print(brieflisting.__str__())
    soldhomes = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD, soldlastdays, selectedhometypes).all()

    housesoldpriceaverage={}
    for brieflisting in soldhomes:
        try:
            # Create dynamic key based on bedrooms and bathrooms
            bed_bath_key = f"{int(brieflisting.bedrooms)}bed{int(brieflisting.bathrooms)}bath"
            # Initialize the dictionary for this key if it doesn't already exist
            if bed_bath_key not in housesoldpriceaverage:
                housesoldpriceaverage[bed_bath_key] = {
                    "count": 0,
                    "totalprice": 0,
                    "houses": []
                }

            # Update the values for the current key
            housesoldpriceaverage[bed_bath_key]["count"] += 1
            housesoldpriceaverage[bed_bath_key]["totalprice"] += brieflisting.price
            housesoldpriceaverage[bed_bath_key]["houses"].append(brieflisting)
        except Exception as e:
            print(f"Error processing brieflisting: {e}")
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

    return housesoldpriceaverage, soldhomes

def AreaReportModelRunForSale(selected_zones, selectedhometypes,onsaledays):
    unfiltered_brieflistings = []
    zone_ids=[]
    for zone in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zone)
        if wzone:
            zone_ids.append(wzone.id)
            # unfiltered_brieflistings=unfiltered_brieflistings+wzone.brief_listings

    # current_time_ms = int(datetime.now().timestamp())  # Current time in milliseconds
    # time_threshold_ms = current_time_ms - (onsaledays * 24 * 60 * 60 )

    # forsalebrieflistings=[]
    # for brieflisting in unfiltered_brieflistings:
    #     try:
    #         if brieflisting.homeType not in selectedhometypes:
    #             continue
    #         if brieflisting.homeStatus!=FOR_SALE:
    #             continue
    #         if brieflisting.listtime < time_threshold_ms:  # Check if the listing is older than the threshold
    #             continue
    #         forsalebrieflistings.append(brieflisting)
    #     except Exception as e:
    #         print(f"Error processing brieflisting: {e}")

    forsalebrieflistings = brieflistingcontroller.listingsByZonesandStatus(zone_ids, FOR_SALE, onsaledays, selectedhometypes).all()
    housesoldpriceaverage={}
    # for brieflisting in forsalebrieflistings:
    #     try:
    #         # Create dynamic key based on bedrooms and bathrooms
    #         bed_bath_key = f"{int(brieflisting.bedrooms)}bed{int(brieflisting.bathrooms)}bath"
    #         # Initialize the dictionary for this key if it doesn't already exist
    #         if bed_bath_key not in housesoldpriceaverage:
    #             housesoldpriceaverage[bed_bath_key] = {
    #                 "count": 0,
    #                 "totalprice": 0,
    #                 "houses": []
    #             }
    #
    #         # Update the values for the current key
    #         housesoldpriceaverage[bed_bath_key]["count"] += 1
    #         housesoldpriceaverage[bed_bath_key]["totalprice"] += brieflisting.price
    #         housesoldpriceaverage[bed_bath_key]["houses"].append(brieflisting)
    #     except Exception as e:
    #         print(f"Error processing brieflisting: {e}")
    # # Create a map centered around Ballard, Seattle
    #
    # for key, value in housesoldpriceaverage.items():
    #     value['minprice']=1000000000
    #     value['maxprice']=0
    #     if value['count']==0:
    #         value['aveprice'] = 'NA'
    #     else:
    #         value['aveprice']= int(value['totalprice']/value['count'])
    #     for brieflisting in value["houses"]:
    #         if brieflisting.price<value['minprice']:
    #             value['minprice'] = brieflisting.price
    #         if brieflisting.price>value['maxprice']:
    #             value['maxprice'] = brieflisting.price



    return housesoldpriceaverage, forsalebrieflistings



def displayModel(neighbourhoods, selectedhometypes):
    unfiltered_soldhomes=brieflistingcontroller.ListingsByNeighbourhoodsAndHomeTypes(neighbourhoods, selectedhometypes, 30, 'RECENTLY_SOLD')
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
    ax1.set_xlim(0, 100)
    ax1.grid(which='major', linestyle='-', linewidth='0.5', color='blue')
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
