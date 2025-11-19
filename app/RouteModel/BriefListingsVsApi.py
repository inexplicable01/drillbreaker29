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
    try:
        customerzpids = customerzpidcontroller.getCustomerZpidByZpid(api_zpid)
        if not customerzpids:
            return

        old_price = brieflistdb.price
        new_price = apibrieflisting.price
        old_status = brieflistdb.homeStatus
        new_status = apibrieflisting.homeStatus

        # Nicely formatted status labels
        STATUS_LABELS = {
            "FOR_SALE": "For Sale",
            "PENDING": "Pending",
            "RECENTLYSOLD": "Recently Sold",
            "SOLD": "Sold",
        }

        old_status_label = STATUS_LABELS.get(old_status, old_status.replace("_", " ").title())
        new_status_label = STATUS_LABELS.get(new_status, new_status.replace("_", " ").title())

        change_lines = []

        if old_price != new_price:
            change_lines.append(
                f"• Price: ${old_price:,.0f} → ${new_price:,.0f}"
            )

        if old_status != new_status:
            change_lines.append(
                f"• Status: {old_status_label} → {new_status_label}"
            )

        # Fallback if something triggered the function but we didn’t detect a diff
        if not change_lines:
            change_lines.append("• We detected an update on this property.")

        change_text = "\n".join(change_lines)

        # This is what will show inside the “message-block” in the HTML email
        message = (
            f"{brieflistdb}\n\n"
            f"Here’s what changed:\n"
            f"{change_text}\n\n"
            f"Current status: {new_status_label}\n"
            f"Current price: ${new_price:,.0f}"
        )

        title = f"Update on {brieflistdb}"

        for customerzpid in customerzpids:
            if customerzpid.is_retired:
                continue

            customer = customerzpid.customer  # assumes relationship exists
            print(f"{customer.name} is interested in this property!")

            sendEmailListingChange(
                message=message,
                title=title,
                hdpUrl=brieflistdb.hdpUrl,
                customer=customer,  # passes customer through for personalization
            )

    except Exception as e:
        print(f"Email to customer for {brieflistdb.__str__()} failed.")
        print(e)

    return

