from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.CustomerZpidController import customerzpidcontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID,SearchZillowHomesFSBO, SearchZillowHomesByLocation
from datetime import datetime
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing
from app.RouteModel.EmailModel import sendEmailListingChange

def ZPIDinDBNotInAPI_FORSALE(zpid):
    try:
        brieflist = brieflistingcontroller.get_listing_by_zpid(zpid)
        propertydetail = SearchZillowByZPID(zpid)
        if propertydetail['homeStatus'] == 'PENDING':
            print(
                f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
            print(brieflist)
            brieflist.homeStatus = 'PENDING'
            brieflist.pendday = int(datetime.now().timestamp())
            listresults = ListingLengthbyBriefListing(propertydetail)
            brieflist.updateListingLength(listresults)
            brieflistingcontroller.UpdateBriefListing(brieflist)

        elif propertydetail['homeStatus'] == 'RECENTLY_SOLD':
            print(
                f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
            print(brieflist)
            brieflist.homeStatus = 'RECENTLY_SOLD'
            brieflist.dateSold = int(propertydetail['homeStatus'] / 1000)
            listresults = ListingLengthbyBriefListing(propertydetail)
            brieflist.updateListingLength(listresults)
            brieflistingcontroller.UpdateBriefListing(brieflist)

        else:
            print(f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
            # print(brieflist)
            if propertydetail['homeStatus'] == 'FOR_SALE':
                print(propertydetail['zpid'])  # not sure how the ID checks allow us to get here.
                # this means that the Broad Zillow Search did not yield this guy
                # but zpid did.  Could be a problem with the board search.
                # brieflistingcontroller.addBriefListing(brieflist)
                return
            brieflist.homeStatus = propertydetail['homeStatus']
            brieflistingcontroller.UpdateBriefListing(brieflist)  ###This ONLY updates home status, does not update price
            print(brieflist)
        # print(propertydetail)

    except Exception as e:
        print(e,
              f'Error produced when trying to updating the status of {brieflist} for sale unit.  This is for_sale in DB but not '
              'found anymore on api, so likely pending or sold or taken off market')

def EmailCustomersIfInterested(api_zpid, apibrieflisting, brieflistdb):
    # brieflistdb = brieflistingcontroller.get_listing_by_zpid(api_zpid)
    # if brieflistdb.price != apibrieflisting.price:
#     print(message)
        ## Create a latestPriceChangeTime column set time, update price
    customerzpids = customerzpidcontroller.getCustomerZpidByZpid(api_zpid)
    if customerzpids:
        message = (f"Price Change for {brieflistdb}\nFrom {brieflistdb.price} to {apibrieflisting.price}")
        for customerzpid in customerzpids:
            print(f"{customerzpid.customer.name} is interested in this property!")
            # SendEmail()
            if customerzpid.is_retired:
                continue
            title = f'{brieflistdb.__str__()} has changed.'
            sendEmailListingChange(message, title, brieflistdb.hdpUrl)


    return
