from app.MapTools.MappingTools import generateMap
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
import matplotlib.pyplot as plt

import base64
from io import BytesIO
from app.DBFunc.BriefListingController import brieflistingcontroller
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
# model = load('linear_regression_model.joblib')
def AreaReportGatherData(neighbourhoods, doz):
    # soldbriefarr=[]
    # forsalebriefarr=[]
    count =0



def ListAllNeighhourhoodsByCities(neighbourhoods, doz):
    return brieflistingcontroller.ListingsByCities(neighbourhoods, doz)

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





def AreaReportModelRun(selected_zones, selectedhometypes,doz):
    unfiltered_soldhomes = []
    for zone in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zone)
        if wzone:
            unfiltered_soldhomes=unfiltered_soldhomes+wzone.brief_listings
            for brieflisting in wzone.brief_listings:
                print(brieflisting.__str__())
        # if neighbour is None:
        #     city = washingtoncitiescontroller.getCity(zone)
        ## Gathering the Locations
        # unfiltered_soldhomes = unfiltered_soldhomes + brieflistingcontroller.ListingsByNeighbourhood(neighbourhood, doz)
    ## Gets List of briefhomedataraw
    # for neighbourhood in neighbourhoods:
        ## Gathering the Locations
        # unfiltered_soldhomes = unfiltered_soldhomes + brieflistingcontroller.ListingsByCities(neighbourhood, 30)
    ## Gets List of briefhomedataraw

    soldhomes=[]
    for brieflisting in unfiltered_soldhomes:
        if brieflisting.homeType not in selectedhometypes:
            continue
        soldhomes.append(brieflisting)
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

    return housesoldpriceaverage, plot_url, plot_url2, soldhomes

    #

# generateMap(soldhomes, neighbourhoods, True), soldhomes,
# def ListingLength(soldhouse, Listing, db):
#
#     if soldhouse.list2pendCheck==0

