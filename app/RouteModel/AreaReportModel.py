from app.MapTools.MappingTools import generateMap
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief,FindSoldHomesByNeighbourhood
import matplotlib.pyplot as plt

import base64
from io import BytesIO
from app.DBFunc.BriefListingController import brieflistingcontroller
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# model = load('linear_regression_model.joblib')
def AreaReportGatherData(neighbourhoods, doz):
    soldbrieflistingarr=[]
    count =0
    for neighbourhood in neighbourhoods:
        soldbrieflistingarr=  soldbrieflistingarr+ FindSoldHomesByNeighbourhood(neighbourhood,doz)
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

def AreaReportModelRun(neighbourhoods, selectedhometypes,doz):
    ## Calls zillow data Process
    ## Zillow Data Process puts listing in BriefListing Array
    housesoldpriceaverage = initiateSummarydata()
    unfiltered_soldhomes = []
    for neighbourhood in neighbourhoods:
        ## Gathering the Locations
        unfiltered_soldhomes = unfiltered_soldhomes + brieflistingcontroller.ListingsByNeighbourhood(neighbourhood, doz)
    ## Gets List of briefhomedataraw
    # for neighbourhood in neighbourhoods:
        ## Gathering the Locations
        # unfiltered_soldhomes = unfiltered_soldhomes + brieflistingcontroller.ListingsByCities(neighbourhood, 30)
    ## Gets List of briefhomedataraw

    soldhomes=[]
    for brieflisting in unfiltered_soldhomes:
        if brieflisting.homeType not in selectedhometypes:
            continue
        # if brieflisting.latitude
        if brieflisting.latitude<47.3842:
            continue
        if brieflisting.longitude<-122.03385:
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
    colors = ['grey', 'olive',  'magenta']  # Example colors for 1-5 bedrooms
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
                color = 'purple'
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
    plt.scatter([], [], c='purple', label='>4 Bedrooms')
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='Bedroom Count')
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.minorticks_on()
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='lightgray')

    # Saving the plot to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    plot_url = base64.b64encode(buf.read()).decode('utf-8')


    plt.figure()
    colors = ['blue', 'yellow',  'magenta']  # Example colors for 1-5 bedrooms
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
                color = 'purple'
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
    plt.scatter([], [], c='purple', label='>4 Bedrooms')
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='Bedroom Count')

    # Saving the plot to a bytes buffer
    buf2 = BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)

    plot_url2 = base64.b64encode(buf2.read()).decode('utf-8')

    return generateMap(soldhomes, neighbourhoods, True), soldhomes,housesoldpriceaverage, plot_url, plot_url2


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