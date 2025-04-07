# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE
# from flask import Flask, render_template, make_response
# from weasyprint import HTML
from app.MapTools.MappingTools import WA_geojson_features
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.RouteModel.AIModel import AIModel
from app.DBFunc.AIListingController import ailistingcontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO, SearchZillowHomesByLocation
from datetime import datetime
from app.RouteModel.BriefListingsVsApi import ZPIDinDBNotInAPI_FORSALE, EmailCustomersIfInterested

maintanance_bp = Blueprint('maintanance_bp', __name__, url_prefix='/maintanance')

@maintanance_bp.route('/updateopenhouse', methods=['PATCH'])
def updateopenhouse():
    openhouses = []
    for city in ['Kirkland']:
        for_sale_DB = brieflistingcontroller.forSaleInCity(city)
        arrlen = len(for_sale_DB)
        for ind, brieflisting in enumerate(for_sale_DB):
            propertydata = loadPropertyDataFromBrief(brieflisting)
            try:
                if propertydata['homeType'] == "LOT" or propertydata['homeType'] == "MULTI_FAMILY" or propertydata[
                    'homeType'] == "CONDO":
                    print(f'{ind} of {arrlen}, Not a proper home Type, skip')
                    continue
                if propertydata['resoFacts']['propertyCondition'] == "Under Construction":
                    print('Under Construction, skip')
                    continue
                if propertydata['neighborhoodRegion']['name'] in Config.WRONGNEIGHBORHOODS:
                    print('wrong neighbourhood, skip')
                    continue
                if not propertydata['listingSubType']['isOpenHouse'] and propertydata['daysOnZillow'] < 30:
                    brieflisting.openhouseneed = True
                    openhouses.append(brieflisting)
                    print(f'{ind} of {arrlen},  found open home {brieflisting.zpid}')

                else:
                    brieflisting.openhouseneed = False

                brieflistingcontroller.updateBriefListing(brieflisting)


            except Exception as e:
                print(e, brieflisting)
    return jsonify({'status': 'success', 'message': 'Data gathering complete.',
                    'list': [item.to_dict() for item in openhouses]}), 200


@maintanance_bp.route('/getCityList', methods=['GET'])
def cityList():
    counties = request.args.getlist('county')  # Get list of counties from query parameters

    if counties:
        cities = washingtoncitiescontroller.get_cities_by_county(
            counties)  # Assuming this function filters cities by county
    else:
        cities = washingtoncitiescontroller.getallcities()

    return {"cities": cities}, 200


from app.DBFunc.CustomerZpidController import customerzpidcontroller
from app.RouteModel.EmailModel import sendEmailListingChange


@maintanance_bp.route('/checkInterestedListingsChange', methods=['GET'])
def checkInterestedListingsChange():
    customerzpids = customerzpidcontroller.getAllCustomerzpids()
    for customerzpid in customerzpids:
        if customerzpid.is_retired:
            continue
        brieflisting = brieflistingcontroller.get_listing_by_zpid(customerzpid.zpid)
        print(brieflisting)
        pricechanged, homestatuschanged, message, title = brieflistingcontroller.hasListingChanged(brieflisting)
        if pricechanged or homestatuschanged:
            print('SendEMAIL')
            sendEmailListingChange(message, title, brieflisting.hdpUrl)

    return {"changed and alerted": "changed"}, 200


@maintanance_bp.route('/maintainSoldListings', methods=['PATCH'])
def maintainSoldListings():
    if request.method == 'PATCH':
        try:
            doz = int(request.form.get('doz'))
            city = request.form.get('city')

            # Updating the Sold Properties
            soldbrieflistingarr = []
            soldrawdata = SearchZillowHomesByLocation(city, status="recentlySold", doz=doz)
            for briefhomedata in soldrawdata:
                soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

            solddb = brieflistingcontroller.SoldHomesinSearch_Neigh(search_neigh=city, days_ago=doz)
            solddb_ids = [listing.zpid for listing in solddb]
            newsoldbriefs = []
            zpidofinterest = customerzpidcontroller.getAllCustomerzpids()
            for ccc, brieflisting in enumerate(soldbrieflistingarr):
                if brieflisting.zpid in solddb_ids:
                    ##code to remove brieflisting from soldbriefarr
                    ### solddb_ids are the IDs in the DB, if its in there, then its sold, move on.
                    continue
                if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
                    ## Scenario 1. zpid exists in the API as SOLD. BUT ZPID does EXIST in DB but not as SOLD
                    #  Scenario 2. zpid Exists in the API as sold, but zpid exists in DB
                    try:
                        brieflistinginDB = brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid)

                        if brieflistinginDB.homeStatus == 'PENDING':
                            print(brieflisting.__str__() + ' has changed from Pending to SOLD!!!')
                        elif brieflistinginDB.homeStatus == 'FOR_SALE':
                            print(brieflisting.__str__() + ' has changed from For sale to Sold!!!')
                        if brieflisting.zpid in zpidofinterest:
                            EmailCustomersIfInterested(brieflisting.zpid, brieflisting,
                                                       brieflistinginDB)  ## Create a latestPriceChangeTime column set time, update price
                        brieflistinginDB.homeStatus = brieflisting.homeStatus
                        # print(brieflistinginDB.soldtime)
                        brieflistinginDB.soldprice =brieflisting.price
                        brieflistinginDB.price = brieflisting.price
                        brieflistinginDB.soldtime = brieflisting.soldtime
                        brieflistinginDB.getPropertyData()
                        brieflistinginDB.search_neigh = city

                        brieflistingcontroller.setZoneForBriefListing(brieflisting)
                        if brieflistinginDB.NWMLS_id is None:
                            print(brieflistinginDB)
                        brieflistingcontroller.updateBriefListing(brieflistinginDB)
                    except Exception as e:
                        print(e, brieflisting,
                              'Error produced when trying to updating the status of a sold unit.  This is for_sale in DB but not '
                              'found anymore on api, so likely pending or sold or taken off market')

                    continue
                try:
                    print(f"{ccc} out of {soldbrieflistingarr.__len__()}")
                    brieflisting.getPropertyData()
                    brieflistingcontroller.setZoneForBriefListing(brieflisting)
                    newsoldbriefs.append(brieflisting)  # looking for new sold stuff
                    if len(newsoldbriefs) > 100:
                        brieflistingcontroller.SaveBriefListingArr(
                            newsoldbriefs)  # if its sold then maybe it was pending at some point. This line updates it.
                        newsoldbriefs = []
                except Exception as e:
                    print(e, brieflisting)
            brieflistingcontroller.SaveBriefListingArr(
                newsoldbriefs)  # if its sold then maybe it was pending at some point. This line updates it.
            return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
        except Exception as e:
            # If the function fails, return a failure message with details
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500

@maintanance_bp.route('/maintainPendingListings', methods=['PATCH'])
def maintainPendingListings():
    if request.method == 'PATCH':

        city = request.form.get('city')
        brieflistingpendingdb = brieflistingcontroller.getallPendings(city)
        zpidofinterest = customerzpidcontroller.getAllCustomerzpids()
        for brieflistingdb in brieflistingpendingdb:
            try:
                propertydata = loadPropertyDataFromBrief(brieflistingdb)
                brieflistingapi = BriefListing.CreateBriefListingFromPropertyData(propertydata, None, None, city)
                status = propertydata['homeStatus']
                if status == 'PENDING':
                    print(brieflistingdb.__str__() + ' still pending.')
                    continue
                    # print(brieflisting.__str__() + ' has changed from Pending to SOLD!!!')
                elif status == 'FOR_SALE':
                    print(brieflistingdb.__str__() + ' has changed from For sale to Sold!!!')

                    if brieflistingdb.zpid in zpidofinterest:
                        EmailCustomersIfInterested(brieflistingdb.zpid, brieflistingapi,
                                                   brieflistingdb)  ## Create a latestPriceChangeTime column set time, update price
                    brieflistingdb.homeStatus = status
                    brieflistingdb.getPropertyData()
                    brieflistingdb.search_neigh = city
                    brieflistingcontroller.updateBriefListing(brieflistingdb)
                    continue
                elif status == RECENTLYSOLD:
                    if brieflistingdb.zpid in zpidofinterest:
                        EmailCustomersIfInterested(brieflistingdb.zpid, brieflistingapi,
                                                   brieflistingdb)  ## Create a latestPriceChangeTime column set time, update price
                    brieflistingdb.homeStatus = status
                    brieflistingdb.getPropertyData()
                    brieflistingdb.search_neigh = city
                    brieflistingdb.soldprice = propertydata['lastSoldPrice']
                    brieflistingdb.soldtime = int(propertydata['dateSold'])/1000
                    brieflistingcontroller.updateBriefListing(brieflistingdb)
            except Exception as e:
                print(e, brieflistingdb)
    return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200


@maintanance_bp.route('/maintainFORSALEListings', methods=['PATCH'])
def maintainForSaleListings():
    if request.method == 'PATCH':
        try:
            doz = int(request.form.get('doz'))
            city = request.form.get('city')

            forsalebrieflistingarr = []
            forsalerawdata = SearchZillowHomesByLocation(city, status="forSale", doz="180", timeOnZillow="any")
            for briefhomedata in forsalerawdata:
                forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

            # forsalebrief_ids = [listing.zpid for listing in forsalebrieflistingarr]
            forsaleAPIbrief_dict = {listing.zpid: listing for listing in forsalebrieflistingarr}

            ## This is a good daily check
            count =0
            newsalebriefs = []
            for_sale_DB = brieflistingcontroller.forSaleInSearchNeigh(city)
            forsaledb_ids = [brieflist.zpid for brieflist in for_sale_DB]
            zpidofinterest = customerzpidcontroller.getAllCustomerzpids()
            for api_zpid, brieflisting in forsaleAPIbrief_dict.items():  ##LOOP THROUGH API
                count += 1
                print(count)
                # print(brieflisting.streetAddress)
                if api_zpid in forsaledb_ids:
                    ## If API listing (brieflisting is from API) is in DB already
                    ## This is where you would check if priced change
                    brieflistdb = brieflistingcontroller.get_listing_by_zpid(api_zpid)
                    if brieflistdb.price != brieflisting.price:
                        print(f"Price Change for {brieflistdb}")
                        print(f"From {brieflistdb.price} to {brieflisting.price}")### Is zpid under amusement, if so send alert email
                        if api_zpid in zpidofinterest:
                            EmailCustomersIfInterested(api_zpid, brieflisting, brieflistdb)## Create a latestPriceChangeTime column set time, update price
                        brieflistdb.getPropertyData()
                        brieflistdb.search_neigh = city
                        brieflistdb.price= brieflisting.price
                        brieflistdb.lpctime = datetime.now().timestamp()
                        brieflistingcontroller.UpdateBriefListing(brieflistdb)
                    continue
                ## write code here to do this:  forsaleinarea is a list of ids that are for sale in the database, the forsalebriefarr is a list of brieflistings that are currently on sale as extracted by the API.
                ## if any id in forsaleinarea is not in forsalebriefarr, then that means that id is no longer selling and I have to create an array of that.
                try:
                    ## Brieflisting here is not in DATAbase yet.
                    brieflisting.getPropertyData()
                    brieflisting.search_neigh = city
                    brieflistingcontroller.setZoneForBriefListing(brieflisting)
                    newsalebriefs.append(brieflisting)
                    if len(newsalebriefs) > 10:
                        brieflistingcontroller.SaveBriefListingArr(
                            newsalebriefs)  # if its sold then maybe it was pending at some point. This line updates it.
                        newsalebriefs = []
                except Exception as e:
                    print(e, brieflisting)
            brieflistingcontroller.SaveBriefListingArr(newsalebriefs)

            # for_sale_DB = brieflistingcontroller.forSaleInSearchNeigh(city)
            mismanagedcount = {}
            for brieflisting in for_sale_DB:  ##LOOP THROUGH DATABASE
                if brieflisting.zpid in forsaleAPIbrief_dict.keys():
                    # print(brieflisting.__str__() + ' is still for sale.')
                    continue
                else:  ### if brieflisting, which is in DB, is not in API, t
                    mismanagedcount = ZPIDinDBNotInAPI_FORSALE(brieflisting.zpid, doz, mismanagedcount)

            # If the function successfully completes, return a success message
            return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
        except Exception as e:
            # If the function fails, return a failure message with details
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500


@maintanance_bp.route('/maintainListingsByZone', methods=['GET'])
def maintainListingsByZone():
    zone_id = request.form.get('zone_id')
    print(washingtonzonescontroller.getZonebyID(zone_id))
    zone = washingtonzonescontroller.getZonebyID(zone_id)
    print(zone.brief_listings.__len__())
    print(SearchZillowHomesByZone(zone))
    # soldrawdata = SearchZillowHomesByLocation(city, status="recentlySold", doz=doz)
    return 'Great', 200


@maintanance_bp.route('/listingscheck', methods=['PATCH'])
def listingscheck():
    # This is looking for missing listings.  This feels more like its catching things that fe90 through the hole
    city = request.form.get('city')

    for_sale_DB = brieflistingcontroller.forSaleInCity(city)
    forsaledb_ids = [brieflist.zpid for brieflist in for_sale_DB]
    forsaleapi_ids = []
    try:
        forsalerawdata = SearchZillowHomesByLocation(city, status="forSale", doz="any")
    except Exception as e:
        print(e, city)
    for listing in forsalerawdata:
        brieflist = BriefListing.CreateBriefListing(listing, None, None, city)

        forsaleapi_ids.append(brieflist.zpid)
    # find the ids in forsaledb_ids that are NOT in forsaleapi_ids
    # for_sale_api = SearchZillowHomesByCity(city, lastpage, maxpage,  'forSale')
    ids_in_db_not_in_api = set(forsaledb_ids) - set(forsaleapi_ids)

    for id in list(ids_in_db_not_in_api):  # This takes care of the listings
        ZPIDinDBNotInAPI_FORSALE(id)

    return {"IDs in DB but not in API:": list(ids_in_db_not_in_api)}, 200


@maintanance_bp.route('/fsbo', methods=['PATCH'])
def updatefsbo():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cities = washingtoncitiescontroller.getallcities()
    fsboarr = []
    count = 0
    for city in cities:
        lastpage = 1
        maxpage = 2
        while (maxpage + 1) > lastpage:
            try:
                houseresult, lastpage, maxpage = SearchZillowHomesFSBO(city, lastpage, maxpage, 'forSale')

                fsbolistingarr = []
                for briefhomedata in houseresult:
                    if 'is_forAuction' in briefhomedata['listing_sub_type'].keys():
                        continue
                    # print(briefhomedata['listing_sub_type'])
                    fsbolistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))
            except Exception as e:
                print(e, "seattle")
            fsboarr = fsboarr + fsbolistingarr

        for fsbo in fsboarr:
            # print(fsbo)
            propertydetail = SearchZillowByZPID(fsbo.zpid)
            print(count)
            if 'brokerIdDimension' in propertydetail.keys():
                if propertydetail['brokerIdDimension'] == 'For Sale by Agent':
                    print(propertydetail['address'])
                    continue
                elif propertydetail['brokerIdDimension'] == 'For Sale by Owner':
                    print(propertydetail['address'])
                    fsbo.soldBy = "FSBO"
                    fsbo.hdpUrl = propertydetail['hdpUrl']
                    if brieflistingcontroller.get_listing_by_zpid(fsbo.zpid):
                        brieflistingcontroller.updateBriefListing(fsbo)
                    else:
                        brieflistingcontroller.addBriefListing(fsbo)
                    count += 1

    return f"Committed {count} entires", 200


@maintanance_bp.route('/clients_listing_Recommendation', methods=['patch'])
def clients_listing_Recommendation():
    customer_id = request.args.get("customer_id", type=int, default=None)
    # customer, locations = customerzonecontroller.get_customer_zone(customer_id)
    customer = customerzonecontroller.get_customer(customer_id)

    # Loop through neighborhoods to extract data when city is 'Seattle'
    forsalehomes = brieflistingcontroller.getListingByCustomerPreference(customer, FOR_SALE, 90).all()
    for forsale_bl in forsalehomes:
        propertydata = forsale_bl.getPropertyData()
        brieflistingcontroller.updateBriefListing(forsale_bl)
        ai_response = AIModel(forsale_bl, customer, propertydata)
        likelihood_score = ai_response.get("likelihood_score", 0)
        ai_comment = ai_response.get("reason", "")

        # Save AI results to database
        ailistingcontroller.save_ai_evaluation(
            customer_id=customer_id,
            zpid=forsale_bl.zpid,
            ai_comment=ai_comment,
            likelihood_score=likelihood_score
        )
    return {"Updated Recommendations ": len(forsalehomes)}, 200


@maintanance_bp.route('/updateathing', methods=['post'])
def updateathing():
    # fsbo_listings = brieflistingcontroller.getFSBOListings()
    other = brieflistingcontroller.getListingsWithStatus(1000, 'OTHER')
    for brieflisting in other:
        propertydetail = SearchZillowByZPID(brieflisting.zpid)
        events = ListingLengthbyBriefListing(propertydetail)
        try:
            if events['listdate']:
                brieflisting.listtime = events['listdate'].timestamp()
            if events['penddate']:
                brieflisting.pendday = events['penddate'].timestamp()
            if events['solddate']:
                brieflisting.solddate = events['solddate'].timestamp() * 1000

            if propertydetail['homeStatus'] != 'OTHER':
                brieflisting.homeStatus = propertydetail['homeStatus']
                brieflistingcontroller.updateBriefListing(brieflisting)
        except Exception as e:
            print(e, brieflisting)

    return {"Seattle Neighbourhood_subs updated": other.count()}, 200


@maintanance_bp.route('/updateathing2', methods=['post'])
def updateathing2():
    iter_value = request.args.get('iter')
    listings = brieflistingcontroller.getFirstTenListingsWhereMLSisNull(iter_value)
    for brieflisting in listings:
        brieflisting.getPropertyData()
        brieflistingcontroller.updateBriefListing(brieflisting)

    return {"Seattle Neighbourhood_subs updated": listings.__len__()}, 200


@maintanance_bp.route('/updateathing3', methods=['post'])
def updateathing3():
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    iter_value = request.args.get('iter')
    citylist = request.args.get('city')
    citylist = citylist.split(',') if citylist else []
    listings = brieflistingcontroller.getFirstXListingsWhereZoneisNull(int(iter_value), citylist)
    # tempdict ={}
    # for brieflisting in listings:
    #     tempdict[brieflisting.zpid] = brieflisting


    for brieflisting in listings:
    # brieflisting=brieflistingcontroller.get_listing_by_zpid(48906318)
        brieflisting.getPropertyData()
            # brieflistingcontroller.setZoneForBriefListing(brieflisting)
            # print(brieflisting.zone_id)
            # print(brieflisting)
        brieflistingcontroller.updateBriefListing(brieflisting)
    # brieflistingcontroller.setZoneForBriefListingList(listings)

    return {"Seattle Neighbourhood_subs updated": 'listings.__len__()'}, 200


from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.MapTools.MappingTools import citygeojson_features, WA_geojson_features


@maintanance_bp.route('/updateathing4', methods=['post'])
def updateathing4():
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    # iter_value = request.args.get('iter')
    # washingtonzonescontroller.repair_from_geojson(citygeojson_features,WA_geojson_features, washingtoncitiescontroller)
    washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)

    return {"Seattle Neighbourhood_subs updated": 'listings.__len__()'}, 200


@maintanance_bp.route('/updateathing5', methods=['post'])
def updateathing5():
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    # iter_value = request.args.get('iter')
    zone_id = int(request.args.get('zone_id'))
    listings = (BriefListing.query.filter(BriefListing.zone_id== zone_id)
     .filter(BriefListing.homeStatus == RECENTLYSOLD) .all())

    for brieflisting in listings:

        brieflisting.getPropertyData()
        brieflistingcontroller.setZoneForBriefListing(brieflisting)
        print(brieflisting.zone_id)
        print(brieflisting)
        brieflistingcontroller.updateBriefListing(brieflisting)
        # brieflistingcontroller.setZoneForBriefListingList(listings)


    return {"Seattle Neighbourhood_subs updated": 'listings'}, 200
# @maintanance_bp.route('/export-pdf',methods=['get'])
# def export_pdf():
#     # Render the HTML template
#     rendered_html = render_template('template.html', title="PDF Export")
#
#     # Convert HTML to PDF
#     pdf = HTML(string=rendered_html).write_pdf()
#
#     # Create response to serve as a file download
#     response = make_response(pdf)
#     response.headers['Content-Type'] = 'application/pdf'
#     response.headers['Content-Disposition'] = 'attachment; filename=exported_page.pdf'
#
#     return response


# @maintanance_bp.route('/maintainListings_full', methods=['PATCH'])
# def maintainListings_full():
#     if request.method == 'PATCH':
#         try:
#             doz = int(request.form.get('doz'))
#
#             for city in Config.CITIES:
#                 soldbrieflistingarr = []
#                 soldrawdata = SearchZillowHomesByLocation(city, status="recentlySold", doz=doz)
#                 for briefhomedata in soldrawdata:
#                     soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))
#
#                 forsalebrieflistingarr = []
#                 forsalerawdata = SearchZillowHomesByLocation(city, status="forSale", doz="any")
#                 for briefhomedata in forsalerawdata:
#                     forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))
#
#
#                 forsalebrief_ids = [listing.zpid for listing in forsalebrieflistingarr]
#                 forsaleAPIbrief_dict = {listing.zpid: listing for listing in forsalebrieflistingarr}
#                 for_sale_DB = brieflistingcontroller.forSaleInNeighbourhood(city, doz)
#                 ## This is a good daily check
#                 for brieflisting in for_sale_DB:
#                     if brieflisting.zpid in forsalebrief_ids:
#                         print(brieflisting.__str__() + ' is still for sale.')
#                         continue
#                     try:
#                         status = forsaleAPIbrief_dict[brieflisting.zpid].homeStatus
#                         if status == 'PENDING' or status == 'RECENTLY_SOLD':
#                             brieflisting.homeStatus = status
#                             print(brieflisting.__str__() + ' has changed from Selling to Pending or Sold!!!')
#                             brieflistingcontroller.updateBriefListing(brieflisting)
#                         else:
#                             brieflisting.homeStatus = status
#                             print('Looking into this status ' + status + '  : ' + brieflisting.__str__())
#                     except Exception as e:
#                         print(e, brieflisting)
#
#                 # #Updating the Sold Properties
#                 solddb = brieflistingcontroller.SoldHomesinNeighbourhood(city, doz)
#                 solddb_ids = [listing.zpid for listing in solddb]
#                 newsoldbriefs = []
#
#                 for ccc, brieflisting in enumerate(soldbrieflistingarr):
#                     if brieflisting.zpid in solddb_ids:
#                         ##code to remove brieflisting from soldbriefarr
#                         continue
#                     if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
#                         continue
#                     try:
#                         print(f"{ccc} out of {soldbrieflistingarr.__len__()}")
#                         brieflisting.getPropertyData()
#                         newsoldbriefs.append(brieflisting)  # looking for new sold stuff
#                         if len(newsoldbriefs) > 100 or ccc==len(soldbrieflistingarr)-1:
#                             brieflistingcontroller.SaveBriefListingArr(
#                                 newsoldbriefs)  # if its sold then maybe it was pending at some point. This line updates it.
#                             newsoldbriefs = []
#                     except Exception as e:
#                         print(e, brieflisting)
#
#                 newsalebriefs = []
#                 for brieflisting in forsalebrieflistingarr:
#                     if brieflisting.zpid in forsalebrief_ids:
#                         ##code to remove brieflisting from soldbriefarr
#                         continue
#                     ## write code here to do this:  forsaleinarea is a list of ids that are for sale in the database, the forsalebriefarr is a list of brieflistings that are currently on sale as extracted by the API.
#                     ## if any id in forsaleinarea is not in forsalebriefarr, then that means that id is no longer selling and I have to create an array of that.
#                     try:
#                         brieflisting.getPropertyData()
#                         newsalebriefs.append(brieflisting)
#                     except Exception as e:
#                         print(e, brieflisting)
#                 brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
#             # If the function successfully completes, return a success message
#             return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
#         except Exception as e:
#             # If the function fails, return a failure message with details
#             return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500
