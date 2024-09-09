# email_bp.py
from flask import Blueprint, redirect, url_for
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.config import Config,SW
maintanance_bp = Blueprint('maintanance_bp', __name__, url_prefix='/maintanance')
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief,FindHomesByNeighbourhood, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByCity

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
        while maxpage > lastpage:
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