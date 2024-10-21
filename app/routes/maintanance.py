# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.config import Config,SW
maintanance_bp = Blueprint('maintanance_bp', __name__, url_prefix='/maintanance')
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief,FindHomesByNeighbourhood, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByCity,SearchZillowByZPID,SearchZillowHomesFSBO
from datetime import datetime
@maintanance_bp.route('/neighcleanup', methods=['POST'])
def neighcleanup():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cleanupresults = brieflistingcontroller.listingsN_Cleanup()
    return cleanupresults, 200



@maintanance_bp.route('/updatelistings', methods=['POST'])
def updatelistings():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cities= washingtoncitiescontroller.getallcities()
    for city in cities:
        lastpage = 1
        maxpage = 2
        while (maxpage+1) > lastpage:
            try:
                forsalebrieflistingarr, lastpage, maxpage =  SearchZillowHomesByCity(city, lastpage, maxpage, 'forSale')
            except Exception as e:
                print(e, city)
            forsalebrief_ids = [listing.zpid for listing in forsalebrieflistingarr]
            for_sale_DB = brieflistingcontroller.forSaleInCity(city)

            ##This Loops Throught the Entiries in the DB that are for sale.
            # for brieflisting in for_sale_DB:
            #     if brieflisting.zpid in forsalebrief_ids:
            #         print(brieflisting.__str__() + ' is still for sale.')
            #         continue
            #     try:
            #         status = ListingStatus(brieflisting)
            #         if status == 'PENDING' or status == 'RECENTLY_SOLD':
            #             brieflisting.homeStatus = status
            #             print(brieflisting.__str__() + ' has changed from Selling to Pending or Sold!!!')
            #             brieflistingcontroller.updateBriefListing(brieflisting)
            #         else:
            #             brieflisting.homeStatus = status
            #             print('Looking into this status ' + status + '  : ' + brieflisting.__str__())
            #     except Exception as e:
            #         print(e, brieflisting)
            newsalebriefs = []
            for brieflisting in forsalebrieflistingarr:
                if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
                    ##code to remove brieflisting from soldbriefarr
                    continue
                ## write code here to do this:  forsaleinarea is a list of ids that are for sale in the database, the forsalebriefarr is a list of brieflistings that are currently on sale as extracted by the API.
                ## if any id in forsaleinarea is not in forsalebriefarr, then that means that id is no longer selling and I have to create an array of that.
                try:
                    propertydata = loadPropertyDataFromBrief(brieflisting)
                    brieflisting.hdpUrl = propertydata['hdpUrl']
                    newsalebriefs.append(brieflisting)
                except Exception as e:
                    print(e, brieflisting)
            brieflistingcontroller.SaveBriefListingArr(newsalebriefs)

    return "Done", 200


@maintanance_bp.route('/listingscheck', methods=['PATCH'])
def listingscheck():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cities= washingtoncitiescontroller.getallcities()
    for city in cities:

        for_sale_DB = brieflistingcontroller.forSaleInCity(city)
        forsaledb_ids = [brieflist.zpid  for brieflist in for_sale_DB]
        lastpage = 1
        maxpage = 2
        forsaleapi_ids=[]
        while (maxpage+1)> lastpage:
            try:
                forsalebrieflistingarr, lastpage, maxpage =  SearchZillowHomesByCity(city, lastpage, maxpage, 'forSale')
            except Exception as e:
                print(e, city)
            for listing in forsalebrieflistingarr:
                forsaleapi_ids.append(listing.zpid)
        # find the ids in forsaledb_ids that are NOT in forsaleapi_ids
        # for_sale_api = SearchZillowHomesByCity(city, lastpage, maxpage,  'forSale')
        ids_in_db_not_in_api = set(forsaledb_ids) - set(forsaleapi_ids)

        # If you want it as a list:
        ids_in_db_not_in_api_list = list(ids_in_db_not_in_api)
        for id in ids_in_db_not_in_api_list:
            brieflist = brieflistingcontroller.get_listing_by_zpid(id)
            propertydetail =  SearchZillowByZPID(id)
            if propertydetail['homeStatus']=='PENDING':
                brieflist.homeStatus='PENDING'
                brieflist.pendday=int(datetime.now().timestamp())
                listresults = ListingLengthbyBriefListing(propertydetail)
                brieflist.updateListingLength(listresults)
                brieflistingcontroller.UpdateBriefListing(brieflist)
            elif propertydetail['homeStatus']=='RECENTLY_SOLD':
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
                brieflist.homeStatus = propertydetail['homeStatus']
                brieflistingcontroller.UpdateBriefListing(brieflist)
                print(brieflist)
            # print(propertydetail)


    return {"IDs in DB but not in API:": ids_in_db_not_in_api_list}, 200

@maintanance_bp.route('/fsbo', methods=['POST'])
def updatefsbo():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cities= washingtoncitiescontroller.getallcities()
    fsboarr=[]
    for city in cities:
        lastpage = 1
        maxpage = 2
        while (maxpage+1) > lastpage:
            try:
                fsbolistingarr, lastpage, maxpage =  SearchZillowHomesFSBO(city, lastpage, maxpage, 'forSale')
            except Exception as e:
                print(e, "seattle")
            fsboarr = fsboarr + fsbolistingarr

        count =0
    for fsbo in fsboarr:
        # print(fsbo)
        propertydetail = SearchZillowByZPID(fsbo.zpid)
        # print(propertydetail)
        if 'brokerIdDimension' in propertydetail.keys():
            if propertydetail['brokerIdDimension'] == 'For Sale by Agent':
                # print(propertydetail)
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


# @maintanance_bp.route('/fsbo', methods=['GET'])
# def getfsbo():
#     fsbo_listings = brieflistingcontroller.getFSBOListings()
#     for fsbo in fsbo_listings:
#         # print(fsbo)
#         propertydetail = SearchZillowByZPID(fsbo.zpid)
#         print(propertydetail)
#     return render_template('ForSaleByOwner.html',fsbo_listings=fsbo_listings)