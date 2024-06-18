# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.MapTools.MappingTools import generateMap


def NeighbourhoodReportDetails(neighbourhood):
    # soldhomes = brieflistingcontroller.soldhomes(neighbourhood,30)
    unfiltered_soldhomes = brieflistingcontroller.SoldHomesinNeighbourhood(neighbourhood,   30)
    housesoldpriceaverage = initiateSummarydata()
    price = 0
    for brieflisting in unfiltered_soldhomes:
        if brieflisting is None:
            continue
        price+=brieflisting.price
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

        for key, value in housesoldpriceaverage.items():
            value['minprice'] = 1000000000
            value['maxprice'] = 0
            if value['count'] == 0:
                value['aveprice'] = 'NA'
            else:
                value['aveprice'] = int(value['totalprice'] / value['count'])
            for brieflisting in value["houses"]:
                if brieflisting.price < value['minprice']:
                    value['minprice'] = brieflisting.price
                if brieflisting.price > value['maxprice']:
                    value['maxprice'] = brieflisting.price
    if unfiltered_soldhomes.__len__()==0:
        return 0,{},None
    averageprice = price/unfiltered_soldhomes.__len__()
    map = generateMap(unfiltered_soldhomes, neighbourhood,False);


    return averageprice,housesoldpriceaverage,map


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