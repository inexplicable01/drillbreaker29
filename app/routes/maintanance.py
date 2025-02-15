# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config,SW
#from flask import Flask, render_template, make_response
# from weasyprint import HTML
#from app.MapTools.MappingTools import get_neighborhood_in_Seattle, get_neighborhood_List_in_Seattle
from app.DBFunc.CustomerNeighbourhoodInterestController import customerneighbourhoodinterestcontroller
from app.RouteModel.AIModel import AIModel
from app.DBFunc.AIListingController import ailistingcontroller


maintanance_bp = Blueprint('maintanance_bp', __name__, url_prefix='/maintanance')
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID,SearchZillowHomesFSBO, SearchZillowHomesByLocation
from datetime import datetime
@maintanance_bp.route('/neighcleanup', methods=['POST'])
def neighcleanup():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cleanupresults = brieflistingcontroller.listingsN_Cleanup()
    return cleanupresults, 200



# @maintanance_bp.route('/updatelistings', methods=['POST'])
# def updatelistings():
#     cities= washingtoncitiescontroller.getallcities()
#     for city in cities:
#         lastpage = 1
#         maxpage = 2
#         while (maxpage+1) > lastpage:
#             try:
#                 forsalebrieflistingarr, lastpage, maxpage =  SearchZillowHomesByCity(city, lastpage, maxpage, 'forSale')
#             except Exception as e:
#                 print(e, city)
#             forsalebrief_ids = [listing.zpid for listing in forsalebrieflistingarr]
#             for_sale_DB = brieflistingcontroller.forSaleInCity(city)
#
#             newsalebriefs = []
#             for brieflisting in forsalebrieflistingarr:
#                 if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
#                     ##code to remove brieflisting from soldbriefarr
#                     continue
#                 ## write code here to do this:  forsaleinarea is a list of ids that are for sale in the database, the forsalebriefarr is a list of brieflistings that are currently on sale as extracted by the API.
#                 ## if any id in forsaleinarea is not in forsalebriefarr, then that means that id is no longer selling and I have to create an array of that.
#                 try:
#                     propertydata = loadPropertyDataFromBrief(brieflisting)
#                     brieflisting.hdpUrl = propertydata['hdpUrl']
#                     newsalebriefs.append(brieflisting)
#                 except Exception as e:
#                     print(e, brieflisting)
#             brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
#
#     return "Done", 200

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
                if not propertydata['listingSubType']['isOpenHouse'] and propertydata['daysOnZillow']<30:
                    brieflisting.openhouseneed = True
                    openhouses.append(brieflisting)
                    print(f'{ind} of {arrlen},  found open home {brieflisting.zpid}')

                else:
                    brieflisting.openhouseneed = False

                brieflistingcontroller.updateBriefListing(brieflisting)


            except Exception as e:
                print(e,brieflisting)
    return jsonify({'status': 'success', 'message': 'Data gathering complete.','list':[item.to_dict() for item in openhouses]}), 200

@maintanance_bp.route('/maintainListings_full', methods=['PATCH'])
def maintainListings_full():
    if request.method == 'PATCH':
        try:
            doz = int(request.form.get('doz'))

            for city in Config.CITIES:
                soldbrieflistingarr = []
                soldrawdata = SearchZillowHomesByLocation(city, status="recentlySold", doz=doz)
                for briefhomedata in soldrawdata:
                    soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

                forsalebrieflistingarr = []
                forsalerawdata = SearchZillowHomesByLocation(city, status="forSale", doz="any")
                for briefhomedata in forsalerawdata:
                    forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))


                forsalebrief_ids = [listing.zpid for listing in forsalebrieflistingarr]
                forsaleAPIbrief_dict = {listing.zpid: listing for listing in forsalebrieflistingarr}
                for_sale_DB = brieflistingcontroller.forSaleInNeighbourhood(city, doz)
                ## This is a good daily check
                for brieflisting in for_sale_DB:
                    if brieflisting.zpid in forsalebrief_ids:
                        print(brieflisting.__str__() + ' is still for sale.')
                        continue
                    try:
                        status = forsaleAPIbrief_dict[brieflisting.zpid].homeStatus
                        if status == 'PENDING' or status == 'RECENTLY_SOLD':
                            brieflisting.homeStatus = status
                            print(brieflisting.__str__() + ' has changed from Selling to Pending or Sold!!!')
                            brieflistingcontroller.updateBriefListing(brieflisting)
                        else:
                            brieflisting.homeStatus = status
                            print('Looking into this status ' + status + '  : ' + brieflisting.__str__())
                    except Exception as e:
                        print(e, brieflisting)

                # #Updating the Sold Properties
                solddb = brieflistingcontroller.SoldHomesinNeighbourhood(city, doz)
                solddb_ids = [listing.zpid for listing in solddb]
                newsoldbriefs = []

                for ccc, brieflisting in enumerate(soldbrieflistingarr):
                    if brieflisting.zpid in solddb_ids:
                        ##code to remove brieflisting from soldbriefarr
                        continue
                    if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
                        continue
                    try:
                        print(f"{ccc} out of {soldbrieflistingarr.__len__()}")
                        brieflisting.getPropertyData()
                        newsoldbriefs.append(brieflisting)  # looking for new sold stuff
                        if len(newsoldbriefs) > 100 or ccc==len(soldbrieflistingarr)-1:
                            brieflistingcontroller.SaveBriefListingArr(
                                newsoldbriefs)  # if its sold then maybe it was pending at some point. This line updates it.
                            newsoldbriefs = []
                    except Exception as e:
                        print(e, brieflisting)

                newsalebriefs = []
                for brieflisting in forsalebrieflistingarr:
                    if brieflisting.zpid in forsalebrief_ids:
                        ##code to remove brieflisting from soldbriefarr
                        continue
                    ## write code here to do this:  forsaleinarea is a list of ids that are for sale in the database, the forsalebriefarr is a list of brieflistings that are currently on sale as extracted by the API.
                    ## if any id in forsaleinarea is not in forsalebriefarr, then that means that id is no longer selling and I have to create an array of that.
                    try:
                        brieflisting.getPropertyData()
                        newsalebriefs.append(brieflisting)
                    except Exception as e:
                        print(e, brieflisting)
                brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
            # If the function successfully completes, return a success message
            return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
        except Exception as e:
            # If the function fails, return a failure message with details
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500

@maintanance_bp.route('/getCityList', methods=['GET'])
def cityList():
    return {"cities":washingtoncitiescontroller.getallcities()}, 200

@maintanance_bp.route('/maintainListings', methods=['PATCH'])
def maintainListings():
    if request.method == 'PATCH':
        try:
            doz = int(request.form.get('doz'))
            city= request.form.get('city')

            soldbrieflistingarr = []
            soldrawdata = SearchZillowHomesByLocation(city, status="recentlySold", doz=doz)
            for briefhomedata in soldrawdata:
                soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

            forsalebrieflistingarr = []
            forsalerawdata = SearchZillowHomesByLocation(city, status="forSale", doz="any", timeOnZillow="any")
            for briefhomedata in forsalerawdata:
                forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

            forsalebrief_ids = [listing.zpid for listing in forsalebrieflistingarr]
            forsaleAPIbrief_dict = {listing.zpid: listing for listing in forsalebrieflistingarr}
            for_sale_DB = brieflistingcontroller.forSaleInNeighbourhood(city, doz)
            ## This is a good daily check
            for brieflisting in for_sale_DB:
                if brieflisting.zpid in forsalebrief_ids:
                    print(brieflisting.__str__() + ' is still for sale.')
                    continue
                try:
                    status = forsaleAPIbrief_dict[brieflisting.zpid].homeStatus
                    brieflisting.homeStatus = status
                    if status == 'PENDING':
                        print(brieflisting.__str__() + ' has changed from Selling to Pending!!!')
                        brieflisting.pendday = datetime.utcnow().timestamp()
                    elif status == 'RECENTLY_SOLD':
                        print(brieflisting.__str__() + ' has changed from Selling to Sold!!!')
                    else:
                        print('Looking into this status ' + status + '  : ' + brieflisting.__str__())
                    brieflistingcontroller.updateBriefListing(brieflisting)
                except Exception as e:
                    print(e, brieflisting)

            # #Updating the Sold Properties
            solddb = brieflistingcontroller.SoldHomesinNeighbourhood(city, doz)
            solddb_ids = [listing.zpid for listing in solddb]
            newsoldbriefs = []

            for ccc, brieflisting in enumerate(soldbrieflistingarr):
                if brieflisting.zpid in solddb_ids:
                    ##code to remove brieflisting from soldbriefarr
                    ### solddb_ids are the IDs in the DB, if its in there, then its sold, move on.
                    continue
                if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
                    ## I forgot why I put this here.   But if we got here, this means this zpid,
                    # is not in DB in "city"...so maybe this is to check this zpid isn't in the DB at all.
                    continue
                try:
                    print(f"{ccc} out of {soldbrieflistingarr.__len__()}")
                    brieflisting.getPropertyData()
                    newsoldbriefs.append(brieflisting)  # looking for new sold stuff
                    if len(newsoldbriefs) > 100:
                        brieflistingcontroller.SaveBriefListingArr(
                            newsoldbriefs)  # if its sold then maybe it was pending at some point. This line updates it.
                        newsoldbriefs = []
                except Exception as e:
                    print(e, brieflisting)
            brieflistingcontroller.SaveBriefListingArr(
                newsoldbriefs)  # if its sold then maybe it was pending at some point. This line updates it.

            newsalebriefs = []
            for_sale_DB = brieflistingcontroller.forSaleInCity(city)
            forsaledb_ids = [brieflist.zpid for brieflist in for_sale_DB]
            for brieflisting in forsalebrieflistingarr:
                # print(brieflisting.streetAddress)
                if "Aurora" in brieflisting.streetAddress:
                    print(brieflisting.streetAddress)
                if "Crockett" in brieflisting.streetAddress:
                    print(brieflisting.streetAddress)
                if brieflisting.zpid in forsaledb_ids:
                    ##code to remove brieflisting from soldbriefarr
                    continue
                ## write code here to do this:  forsaleinarea is a list of ids that are for sale in the database, the forsalebriefarr is a list of brieflistings that are currently on sale as extracted by the API.
                ## if any id in forsaleinarea is not in forsalebriefarr, then that means that id is no longer selling and I have to create an array of that.
                try:
                    brieflisting.getPropertyData()
                    newsalebriefs.append(brieflisting)
                except Exception as e:
                    print(e, brieflisting)
            brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
            # If the function successfully completes, return a success message
            return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
        except Exception as e:
            # If the function fails, return a failure message with details
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500

@maintanance_bp.route('/listingscheck', methods=['PATCH'])
def listingscheck():
    # This is looking for missing listings.  This feels more like its catching things that fell through the hole
    city = request.form.get('city')

    for_sale_DB = brieflistingcontroller.forSaleInCity(city)
    forsaledb_ids = [brieflist.zpid  for brieflist in for_sale_DB]
    forsaleapi_ids=[]
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

    ids_in_db_not_in_api_list = list(ids_in_db_not_in_api)
    for id in ids_in_db_not_in_api_list:  #This takes care of the listings
        try:
            brieflist = brieflistingcontroller.get_listing_by_zpid(id)
            propertydetail =  SearchZillowByZPID(id)
            if propertydetail['homeStatus']=='PENDING':
                print(
                    f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
                print(brieflist)
                brieflist.homeStatus='PENDING'
                brieflist.pendday=int(datetime.now().timestamp())
                listresults = ListingLengthbyBriefListing(propertydetail)
                brieflist.updateListingLength(listresults)
                brieflistingcontroller.UpdateBriefListing(brieflist)

            elif propertydetail['homeStatus']=='RECENTLY_SOLD':
                print(
                    f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
                print(brieflist)
                brieflist.homeStatus='RECENTLY_SOLD'
                brieflist.dateSold=int(datetime.now().timestamp() * 1000)
                listresults = ListingLengthbyBriefListing(propertydetail)
                brieflist.updateListingLength(listresults)
                brieflistingcontroller.UpdateBriefListing(brieflist)

            else:
                print(f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
                # print(brieflist)
                if propertydetail['homeStatus']=='FOR_SALE':
                    print(propertydetail['zpid'])#not sure how the ID checks allow us to get here.
                    # brieflistingcontroller.addBriefListing(brieflist)
                brieflist.homeStatus = propertydetail['homeStatus']
                brieflistingcontroller.UpdateBriefListing(brieflist)
                print(brieflist)
            # print(propertydetail)
        except Exception as e:
            print(e, brieflist)

    return {"IDs in DB but not in API:": ids_in_db_not_in_api_list}, 200

@maintanance_bp.route('/fsbo', methods=['PATCH'])
def updatefsbo():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cities= washingtoncitiescontroller.getallcities()
    fsboarr=[]
    count = 0
    for city in cities:
        lastpage = 1
        maxpage = 2
        while (maxpage+1) > lastpage:
            try:
                houseresult, lastpage, maxpage =  SearchZillowHomesFSBO(city, lastpage, maxpage, 'forSale')

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
                    fsbo.soldBy="FSBO"
                    fsbo.hdpUrl = propertydetail['hdpUrl']
                    if brieflistingcontroller.get_listing_by_zpid(fsbo.zpid):
                        brieflistingcontroller.updateBriefListing(fsbo)
                    else:
                        brieflistingcontroller.addBriefListing(fsbo)
                    count +=1


    return f"Committed {count} entires", 200

@maintanance_bp.route('/clients_listing_Recommendation', methods=['patch'])
def clients_listing_Recommendation():
    customer_id = 3
    customer, locations = customerneighbourhoodinterestcontroller.get_customer_neighbourhood_interest(customer_id)
    customer = customerneighbourhoodinterestcontroller.get_customer(customer_id)

    forsalehomes=[]
    margin=100
    # Loop through neighborhoods to extract data when city is 'Seattle'
    for area in locations:
        city_name = area["city"]  # Assuming `city` is in the returned dictionary

        if city_name == "Seattle":
            # Query the database to fetch the full row for this neighborhood
            forsalehomes= forsalehomes + brieflistingcontroller.forSaleListingsByCity(city_name, 365,
                                                                                      maxprice=customer.maxprice + 100000,
                                                                                      minprice=customer.minprice - 100000,
                                                                                      neighbourhood_sub=area["neighbourhood_sub"]).all()
        else:
            forsalehomes= forsalehomes + brieflistingcontroller.forSaleListingsByCity(city_name,
                                                                                      365,
                                                                                      maxprice=customer.maxprice+100000,
                                                                                      minprice=customer.minprice-100000).all()

    for forsale_bl in forsalehomes:
        ai_response = AIModel(forsale_bl.zpid, customer, locations)
        likelihood_score = ai_response.get("likelihood_score", 0)
        ai_comment = ai_response.get("reason", "")

            # Save AI results to database
        ailistingcontroller.save_ai_evaluation(
            customer_id=customer_id,
            zpid=forsale_bl.zpid,
            ai_comment=ai_comment,
            likelihood_score=likelihood_score
        )
    return {"Updated Recommendations ":len(forsalehomes)}, 200

@maintanance_bp.route('/updateathing', methods=['post'])
def updateathing():
    # fsbo_listings = brieflistingcontroller.getFSBOListings()
    other = brieflistingcontroller.getListingsWithStatus(1000,'OTHER')
    for brieflisting in other:
        propertydetail = SearchZillowByZPID(brieflisting.zpid)
        events = ListingLengthbyBriefListing(propertydetail)
        try:
            if events['listdate']:
                brieflisting.listtime = events['listdate'].timestamp()
            if events['penddate']:
                brieflisting.pendday = events['penddate'].timestamp()
            if events['solddate']:
                brieflisting.solddate = events['solddate'].timestamp()*1000

            if propertydetail['homeStatus'] != 'OTHER':
                brieflisting.homeStatus=propertydetail['homeStatus']
                brieflistingcontroller.updateBriefListing(brieflisting)
        except Exception as e:
            print(e, brieflisting)


    return {"Seattle Neighbourhood_subs updated":other.count()}, 200

@maintanance_bp.route('/updateathing2', methods=['post'])
def updateathing2():
    listings = brieflistingcontroller.getFirstTenListingsWhereMLSisNull()
    for brieflisting in listings:
        brieflisting.getPropertyData()
        brieflistingcontroller.updateBriefListing(brieflisting)

    return {"Seattle Neighbourhood_subs updated":listings.__len__()}, 200


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