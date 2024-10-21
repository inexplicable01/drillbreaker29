# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.config import Config,SW
fsbo_bp = Blueprint('fsbo_bp', __name__, url_prefix='/fsbo')
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief,FindHomesByNeighbourhood, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByCity,SearchZillowByZPID,SearchZillowHomesFSBO
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from app.DBModels.FSBOStatus import FSBOStatus

def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in miles
    R = 3959.87433

    # Convert degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in miles

    return distance

@fsbo_bp.route('/fsbo', methods=['GET'])
def getfsbo():
    fsbo_listings = brieflistingcontroller.getFSBOListings()

    return render_template('ForSaleByOwner.html',fsbo_listings=selectedListing(fsbo_listings))


@fsbo_bp.route('/updatefsbolisting', methods=['POST'])
def updatefsbolisting():
    try:
        zpid = request.form.get('zpid')
        details = request.form.get('details')
        has_contacted_online = 'hasContactedOnline' in request.form
        has_post_carded = 'hasPostCarded' in request.form
        # Fetch the listing by zpid
        listing = brieflistingcontroller.get_listing_by_zpid(zpid)

        if listing:
            # Update waybercomments
            listing.waybercomments = details

            # Check if FSBOStatus exists, if not, create it
            if not listing.fsbo_status:
                fsbo_status = FSBOStatus(zpid=listing.zpid)
                # db.session.add(fsbo_status)
            else:
                fsbo_status = listing.fsbo_status

        fsbo_status.hasContactedOnline = has_contacted_online
        fsbo_status.hasPostCarded = has_post_carded
        listing.waybercomments = details

        brieflistingcontroller.updateBriefListing(listing,fsbo_status)
        # print(listing)
        # print(details)
    except Exception as e:
        # db.session.rollback()
        print(f'Error updating listing: {str(e)}', 'danger')

    fsbo_listings = brieflistingcontroller.getFSBOListings()


    return render_template('ForSaleByOwner.html',fsbo_listings=selectedListing(fsbo_listings))


def selectedListing(fsbo_listings):
    seattle_latitude = 47.6062
    seattle_longitude = -122.3321

    # Filter listings by county and distance
    filtered_fsbo_listings = [
        listing for listing in fsbo_listings
        if listing.city in ['King', 'Pierce', 'Snohomish'] or
        calculate_distance(listing.latitude, listing.longitude, seattle_latitude, seattle_longitude) <= 60
    ]
    untouched =[]
    touched_wcommentsonly =[]
    touched_andcontacted = []
    for listing in filtered_fsbo_listings:
        if not listing.fsbo_status and not listing.waybercomments:
            untouched.append(listing)
        elif not listing.fsbo_status and listing.waybercomments:
            touched_wcommentsonly.append(listing)
        else:
            if not listing.fsbo_status.hasContactedOnline and not listing.fsbo_status.hasPostCarded and listing.waybercomments:
                touched_andcontacted.append(listing)
            elif listing.fsbo_status.hasContactedOnline or listing.fsbo_status.hasPostCarded:
                touched_andcontacted.append(listing)
            else:
                untouched.append(listing)

    return untouched + touched_wcommentsonly +touched_andcontacted