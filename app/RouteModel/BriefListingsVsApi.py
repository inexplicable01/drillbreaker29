from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.CustomerZpidController import customerzpidcontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID,SearchZillowHomesFSBO
from datetime import datetime
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing
from app.RouteModel.EmailModel import sendEmailListingChange

def ZPIDinDBNotInAPI_FORSALE(zpid, doz, mismanagedcount):
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
            brieflistingcontroller.updateBriefListing(brieflist)

        elif propertydetail['homeStatus'] == 'RECENTLY_SOLD':
            print(
                f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
            print(brieflist)
            brieflist.homeStatus = 'RECENTLY_SOLD'
            brieflist.dateSold = int(propertydetail['homeStatus'] / 1000)
            listresults = ListingLengthbyBriefListing(propertydetail)
            brieflist.updateListingLength(listresults)
            brieflistingcontroller.updateBriefListing(brieflist)

        else:

            # print(brieflist)
            if propertydetail['homeStatus'] == 'FOR_SALE':
                days = propertydetail.get('daysOnZillow')
                if days is not None:
                    try:
                        if int(days) > doz:
                            print(f"Listing {brieflist} has been on the market for {days} days — flag it.")
                            return mismanagedcount
                    except (TypeError, ValueError):
                        print(f"Warning: Could not parse daysOnZillow for listing {brieflist}")
                print(
                    f" brieflist status {brieflist.homeStatus} , propertydetail status {propertydetail['homeStatus']}")
                print(f"Not sure how we got here.  Need to continue to monitor.zpid : {propertydetail['zpid']}")
                mismanagedcount[brieflist.zpid]=propertydetail
                brieflist.getPropertyData()
                brieflistingcontroller.updateBriefListing(brieflist)
                return mismanagedcount
            brieflist.homeStatus = propertydetail['homeStatus']
            brieflistingcontroller.updateBriefListing(brieflist)  ###This ONLY updates home status, does not update price
            print(brieflist)
        # print(propertydetail)

    except Exception as e:
        print(e,
              f'Error produced when trying to updating the status of {brieflist} for sale unit.  This is for_sale in DB but not '
              'found anymore on api, so likely pending or sold or taken off market')
    return mismanagedcount

def EmailCustomersIfInterested(api_zpid, apibrieflisting, brieflistdb):
    # brieflistdb = brieflistingcontroller.get_listing_by_zpid(api_zpid)
    # if brieflistdb.price != apibrieflisting.price:
#     print(message)
        ## Create a latestPriceChangeTime column set time, update price
    try:
        customerzpids = customerzpidcontroller.getCustomerZpidByZpid(api_zpid)
        if customerzpids:
            message = (f"Price Change for {brieflistdb}\nFrom {brieflistdb.price} to {apibrieflisting.price}\n"
                       f"Status went from {brieflistdb.homeStatus} to {apibrieflisting.homeStatus}")
            for customerzpid in customerzpids:
                print(f"{customerzpid.customer.name} is interested in this property!")
                # SendEmail()
                if customerzpid.is_retired:
                    continue
                title = f'{brieflistdb.__str__()} has changed.'
                sendEmailListingChange(message, title, brieflistdb.hdpUrl)
    except Exception as e:
        print(f'Email to customer for {brieflistdb.__str__()} failed.')
        print(e)

    return
