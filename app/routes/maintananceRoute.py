# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, render_template, request
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBModels.BriefListing import BriefListing
from app.config import Config, SW, RECENTLYSOLD, FOR_SALE
# from flask import Flask, render_template, make_response
# from weasyprint import HTML
# from app.MapTools.MappingTools import WA_geojson_features
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.RouteModel.AIModel import AIModel
from app.DBFunc.AIListingController import ailistingcontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowHomesByZone
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief, ListingStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID, SearchZillowHomesFSBO, SearchZillowHomesByLocation
from datetime import datetime
from app.RouteModel.BriefListingsVsApi import ZPIDinDBNotInAPI_FORSALE, EmailCustomersIfInterested
from app.config import RECENTLYSOLD, LIKELYSOLDWITHOUTAGENTS, OTHER, AUCTIONITEM, FOR_RENT
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
from app.useful_func import print_and_log


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


from app.DBFunc.CustomerController import customercontroller


@maintanance_bp.route('/checkCustomerTrackedListings', methods=['GET'])
def checkCustomerTrackedListings():
    """
    Check all customer-tracked listings for changes since last check.
    Sends email alerts when changes are detected.
    Uses CustomerZpid table directly for tracking.
    """
    stats = {
        'total_tracked': 0,
        'checked': 0,
        'changes_detected': 0,
        'alerts_sent': 0,
        'errors': 0
    }

    # Get all active customer-listing pairs
    customerzpids = customerzpidcontroller.getAllCustomerzpids()

    for customerzpid in customerzpids:
        stats['total_tracked'] += 1

        # Skip retired interests
        if customerzpid.is_retired:
            continue

        try:
            # Get current listing state
            current_listing = brieflistingcontroller.get_listing_by_zpid(customerzpid.zpid)
            if not current_listing:
                customer_name = f"{customerzpid.customer.name} {customerzpid.customer.lastname}" if customerzpid.customer else "Unknown"
                print_and_log(f"[ERROR] Customer {customerzpid.customer_id} ({customer_name}), zpid {customerzpid.zpid} - listing not found in database")
                stats['errors'] += 1
                continue

            stats['checked'] += 1

            # Check if this is first time checking (no snapshot yet)
            if customerzpid.last_price is None and customerzpid.last_home_status is None:
                # First time - create initial snapshot
                customerzpidcontroller.update_listing_snapshot(customerzpid, current_listing)
                customer_name = f"{customerzpid.customer.name} {customerzpid.customer.lastname}" if customerzpid.customer else "Unknown"
                print_and_log(f"[NEW] Customer {customerzpid.customer_id} ({customer_name}), zpid {customerzpid.zpid} - initial snapshot created (${current_listing.price:,}, {current_listing.homeStatus})")
            else:
                # Compare current state to last known state
                change_result = customerzpid.detect_changes(current_listing)

                if change_result['has_changes']:
                    stats['changes_detected'] += 1
                    changes_list = change_result['changes']

                    customer_name = f"{customerzpid.customer.name} {customerzpid.customer.lastname}" if customerzpid.customer else "Unknown"
                    print_and_log(f"[CHANGE] Customer {customerzpid.customer_id} ({customer_name}), zpid {customerzpid.zpid} - {'; '.join(changes_list)}")

                    # Get customer info
                    customer = customercontroller.getCustomerByID(customerzpid.customer_id)

                    if customer:
                        # Build change message
                        message = f"Property Update: {current_listing.streetAddress}, {current_listing.city}\n\n"
                        message += "Changes:\n" + "\n".join(f"- {change}" for change in changes_list)

                        title = f"Listing Update: {current_listing.streetAddress}"

                        # Send email alert (using your email for testing)
                        sendEmailListingChange(
                            message=message,
                            title=title,
                            hdpUrl=current_listing.hdpUrl,
                            customer=customer
                        )

                        stats['alerts_sent'] += 1

                        # Mark that we sent an alert
                        customerzpidcontroller.mark_listing_alerted(customerzpid)

                    # Update snapshot with new state
                    customerzpidcontroller.update_listing_snapshot(customerzpid, current_listing, changes_detected=changes_list)
                else:
                    # No changes, just update the last_checked timestamp
                    customer_name = f"{customerzpid.customer.name} {customerzpid.customer.lastname}" if customerzpid.customer else "Unknown"
                    print_and_log(f"[OK] Customer {customerzpid.customer_id} ({customer_name}), zpid {customerzpid.zpid} - no changes (${current_listing.price:,}, {current_listing.homeStatus})")
                    customerzpidcontroller.update_listing_snapshot(customerzpid, current_listing)

        except Exception as e:
            customer_name = f"{customerzpid.customer.name} {customerzpid.customer.lastname}" if customerzpid.customer else "Unknown"
            print_and_log(f"[ERROR] Customer {customerzpid.customer_id} ({customer_name}), zpid {customerzpid.zpid}: {e}")
            stats['errors'] += 1
            continue

    return jsonify({
        'status': 'success',
        'stats': stats,
        'message': f"Checked {stats['checked']} listings, detected {stats['changes_detected']} changes, sent {stats['alerts_sent']} alerts"
    }), 200


@maintanance_bp.route('/maintainSoldListings', methods=['PATCH'])
def maintainSoldListings():
    if request.method == 'PATCH':
        zonepolygons = washingtonzonescontroller.load_zone_polygons()
        try:
            doz = int(request.form.get('doz'))
            city = request.form.get('city')
            max_sqft=10000
            # Track stats for email report
            stats = {
                'city': city,
                'total_api_results': 0,
                'new_sold': 0,
                'pending_to_sold': 0,
                'forsale_to_sold': 0,
                'customer_alerts_sent': 0,
                'errors': 0,
                'pending_to_sold_list': [],  # List of properties with addresses
                'forsale_to_sold_list': []   # List of properties with addresses
            }

            # Updating the Sold Properties
            soldbrieflistingarr = []
            soldrawdata = SearchZillowHomesByLocation(city, status="Sold", max_sqft = max_sqft)
            stats['total_api_results'] = len(soldrawdata)

            for briefhomedata in soldrawdata:
                soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

            solddb = brieflistingcontroller.SoldHomesinSearch_Neigh(search_neigh=city, days_ago=doz)
            solddb_ids = [listing.zpid for listing in solddb]
            newsoldbriefs = []
            zpidofinterest = customerzpidcontroller.getAllZPIDS_Customerzpids()

            for ccc, brieflisting in enumerate(soldbrieflistingarr):
                # if ccc>10:
                #     break
                if brieflisting.zpid in solddb_ids:
                    continue
                brieflistinginDB = brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid)
                if brieflistinginDB is not None:
                    try:
                        if brieflistinginDB.homeStatus == 'PENDING':
                            print(brieflisting.__str__() + ' has changed from Pending to SOLD!!!')
                            stats['pending_to_sold'] += 1
                            stats['pending_to_sold_list'].append({
                                'address': f"{brieflisting.streetAddress}, {brieflisting.city}",
                                'zpid': brieflisting.zpid,
                                'price': brieflisting.price
                            })
                        elif brieflistinginDB.homeStatus == 'FOR_SALE':
                            print(brieflisting.__str__() + ' has changed from For sale to Sold!!!')
                            stats['forsale_to_sold'] += 1
                            stats['forsale_to_sold_list'].append({
                                'address': f"{brieflisting.streetAddress}, {brieflisting.city}",
                                'zpid': brieflisting.zpid,
                                'price': brieflisting.price
                            })

                        if brieflisting.zpid in zpidofinterest:
                            EmailCustomersIfInterested(brieflisting.zpid, brieflisting, brieflistinginDB)
                            stats['customer_alerts_sent'] += 1

                        brieflistinginDB.homeStatus = brieflisting.homeStatus
                        brieflistinginDB.soldprice = brieflisting.price
                        brieflistinginDB.price = brieflisting.price
                        brieflistinginDB.soldtime = brieflisting.soldtime
                        brieflistinginDB.getPropertyData()
                        brieflistinginDB.search_neigh = city

                        brieflistingcontroller.setZoneForBriefListing(brieflisting, zonepolygons)
                        if brieflistinginDB.NWMLS_id is None:
                            print(brieflistinginDB)
                        brieflistingcontroller.updateBriefListing(brieflistinginDB)
                    except Exception as e:
                        print(e, brieflisting, 'Error updating sold unit')
                        stats['errors'] += 1
                    continue

                try:
                    print(f"{ccc} out of {soldbrieflistingarr.__len__()}")
                    brieflisting.getPropertyData()
                    brieflistingcontroller.setZoneForBriefListing(brieflisting, zonepolygons)
                    newsoldbriefs.append(brieflisting)
                    stats['new_sold'] += 1

                    if len(newsoldbriefs) > 100:
                        brieflistingcontroller.SaveBriefListingArr(newsoldbriefs)
                        newsoldbriefs = []
                except Exception as e:
                    print(e, brieflisting)
                    stats['errors'] += 1

            brieflistingcontroller.SaveBriefListingArr(newsoldbriefs)

            return jsonify({
                'status': 'success',
                'message': f'{city} sold listings updated successfully',
                'stats': stats
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'failure',
                'message': 'Data gathering failed.',
                'details': str(e)
            }), 500

@maintanance_bp.route('/maintainPendingListings', methods=['PATCH'])
def maintainPendingListings():
    zonepolygons = washingtonzonescontroller.load_zone_polygons()
    if request.method == 'PATCH':
        city = request.form.get('city')

        # Track stats for email report
        stats = {
            'city': city,
            'total_pending_checked': 0,
            'still_pending': 0,
            'pending_to_forsale': 0,
            'pending_to_sold': 0,
            'customer_alerts_sent': 0,
            'errors': 0,
            'pending_to_forsale_list': [],  # List of properties that went from pending back to for sale
            'pending_to_sold_list': []      # List of properties that went from pending to sold
        }

        brieflistingpendingdb = brieflistingcontroller.getallPendings(city)
        stats['total_pending_checked'] = len(brieflistingpendingdb)
        zpidofinterest = customerzpidcontroller.getAllZPIDS_Customerzpids()

        for brieflistingdb in brieflistingpendingdb:
            try:
                propertydata = loadPropertyDataFromBrief(brieflistingdb)
                brieflistingapi = BriefListing.CreateBriefListingFromPropertyData(propertydata, None, None, city)
                status = propertydata['homeStatus']

                if status == 'PENDING':
                    print(brieflistingdb.__str__() + ' still pending.')
                    stats['still_pending'] += 1
                    continue

                elif status == 'FOR_SALE':
                    print(brieflistingdb.__str__() + ' has changed from Pending to For Sale!!!')
                    stats['pending_to_forsale'] += 1
                    stats['pending_to_forsale_list'].append({
                        'address': f"{brieflistingdb.streetAddress}, {brieflistingdb.city}",
                        'zpid': brieflistingdb.zpid,
                        'price': brieflistingapi.price
                    })

                    if brieflistingdb.zpid in zpidofinterest:
                        EmailCustomersIfInterested(brieflistingdb.zpid, brieflistingapi, brieflistingdb)
                        stats['customer_alerts_sent'] += 1

                    brieflistingdb.homeStatus = status
                    brieflistingdb.getPropertyData()
                    brieflistingdb.search_neigh = city
                    brieflistingcontroller.updateBriefListing(brieflistingdb)
                    continue

                elif status == RECENTLYSOLD:
                    stats['pending_to_sold'] += 1
                    stats['pending_to_sold_list'].append({
                        'address': f"{brieflistingdb.streetAddress}, {brieflistingdb.city}",
                        'zpid': brieflistingdb.zpid,
                        'price': brieflistingapi.price
                    })

                    if brieflistingdb.zpid in zpidofinterest:
                        EmailCustomersIfInterested(brieflistingdb.zpid, brieflistingapi, brieflistingdb)
                        stats['customer_alerts_sent'] += 1

                    brieflistingdb.homeStatus = status
                    brieflistingdb.getPropertyData()
                    brieflistingdb.search_neigh = city
                    listresults = ListingLengthbyBriefListing(propertydata)
                    brieflistingdb.dateSold = listresults['solddate'].timestamp()
                    brieflistingcontroller.updateBriefListing(brieflistingdb)

            except Exception as e:
                print(e, brieflistingdb)
                stats['errors'] += 1

    return jsonify({
        'status': 'success',
        'message': f'{city} pending listings checked successfully',
        'stats': stats
    }), 200


@maintanance_bp.route('/maintainFORSALEListings', methods=['PATCH'])
def maintainForSaleListings():
    zonepolygons = washingtonzonescontroller.load_zone_polygons()
    if request.method == 'PATCH':
        try:
            doz = int(request.form.get('doz'))
            city = request.form.get('city')
            max_sqft=10000
            # Track stats for email report
            stats = {
                'city': city,
                'total_api_results': 0,
                'new_for_sale': 0,
                'price_changes': 0,
                'customer_alerts_sent': 0,
                'mismanaged': 0,
                'errors': 0,
                'new_for_sale_list': [],    # List of new listings that came online
                'price_changes_list': []     # List of listings with price changes
            }

            forsalebrieflistingarr = []
            forsalerawdata = SearchZillowHomesByLocation(city, status="For_Sale", max_sqft=max_sqft)
            stats['total_api_results'] = len(forsalerawdata)

            for briefhomedata in forsalerawdata:
                forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, city))

            forsaleAPIbrief_dict = {listing.zpid: listing for listing in forsalebrieflistingarr}

            count = 0
            newsalebriefs = []
            for_sale_DB = brieflistingcontroller.forSaleInSearchNeigh(city)
            forsaledb_dict = {brieflist.zpid: brieflist for brieflist in for_sale_DB}
            forsaledb_ids = forsaledb_dict.keys()
            zpidofinterest = customerzpidcontroller.getAllZPIDS_Customerzpids()

            for api_zpid, brieflisting in forsaleAPIbrief_dict.items():
                count += 1
                print(count)
                if api_zpid in forsaledb_ids:
                    brieflistdb =forsaledb_dict[api_zpid]
                    if brieflistdb.price != brieflisting.price:
                        print(f"Price Change for {brieflistdb}")
                        print(f"From {brieflistdb.price} to {brieflisting.price}")
                        stats['price_changes'] += 1
                        stats['price_changes_list'].append({
                            'address': f"{brieflistdb.streetAddress}, {brieflistdb.city}",
                            'zpid': brieflistdb.zpid,
                            'old_price': brieflistdb.price,
                            'new_price': brieflisting.price
                        })

                        if api_zpid in zpidofinterest:
                            EmailCustomersIfInterested(api_zpid, brieflisting, brieflistdb)
                            stats['customer_alerts_sent'] += 1

                        brieflistdb.getPropertyData()
                        brieflistdb.search_neigh = city
                        brieflistdb.price = brieflisting.price
                        brieflistdb.lpctime = datetime.now().timestamp()
                        brieflistingcontroller.updateBriefListing(brieflistdb)
                    continue

                try:
                    if brieflisting.homeType=='LOT':
                        continue
                    brieflisting.getPropertyData()
                    brieflisting.search_neigh = city
                    brieflistingcontroller.setZoneForBriefListing(brieflisting, zonepolygons)
                    newsalebriefs.append(brieflisting)
                    stats['new_for_sale'] += 1
                    stats['new_for_sale_list'].append({
                        'address': f"{brieflisting.streetAddress}, {brieflisting.city}",
                        'zpid': brieflisting.zpid,
                        'price': brieflisting.price
                    })

                    if len(newsalebriefs) > 10:
                        brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
                        newsalebriefs = []
                except Exception as e:
                    print(e, brieflisting)
                    stats['errors'] += 1

            brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
            count =0
            mismanageddict = {}
            print(
                "This Loop is going through whats in the database currently.   brieflisting is IN the database as a FOR_SALE")
            for brieflisting in for_sale_DB:
                count += 1
                print(count)
                if brieflisting.zpid in forsaleAPIbrief_dict.keys():
                    #If zpid is in the array from the API, then move on , this was dealt with above already
                    continue
                elif brieflisting.livingArea > max_sqft:
                    print('delete me 32332')
                    continue
                elif brieflisting.waybercomments in ["FSBO-Online.com", "Auction.com 2", AUCTIONITEM]:
                    print(f'WayberComments exclude this {brieflisting}, cause of {brieflisting.waybercomments}')
                    continue
                else:
                    # Check if the missing ones with to pending or SOLD.  the mismanageddict is the dict of brieflistings that I can't find via the API call, even though I expect it to be there.
                    mismanageddict = ZPIDinDBNotInAPI_FORSALE(brieflisting.zpid, doz, mismanageddict)

            stats['mismanaged'] = len(mismanageddict)

            return jsonify({
                'status': 'success',
                'message': f'{city} for-sale listings updated successfully',
                'stats': stats
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'failure',
                'message': 'Data gathering failed.',
                'details': str(e)
            }), 500


@maintanance_bp.route('/maintainSoldListingsByZone', methods=['PATCH'])
def maintainSoldListingsByZone():
    """
    Zone-based version of maintainSoldListings - more cost-efficient than city-based search
    """
    if request.method == 'PATCH':
        zone_id = int(request.form.get('zone_id'))
        soldInLast = request.form.get('soldInLast', '90_days')

        zone = washingtonzonescontroller.getZonebyID(zone_id)
        zonepolygons = washingtonzonescontroller.load_zone_polygons()

        try:
            # Get sold listings from API using zone polygon
            soldbrieflistingarr = []
            soldrawdata = SearchZillowHomesByZone(zone, status="Sold", soldInLast=soldInLast)
            for briefhomedata in soldrawdata:
                soldbrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, zone.City))

            # Get sold listings from DB for this zone
            solddb = BriefListing.query.filter(
                BriefListing.zone_id == zone_id,
                BriefListing.homeStatus == RECENTLYSOLD
            ).all()
            solddb_ids = [listing.zpid for listing in solddb]

            newsoldbriefs = []
            zpidofinterest = customerzpidcontroller.getAllZPIDS_Customerzpids()

            for ccc, brieflisting in enumerate(soldbrieflistingarr):
                if brieflisting.zpid in solddb_ids:
                    continue

                if brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid) is not None:
                    try:
                        brieflistinginDB = brieflistingcontroller.get_listing_by_zpid(brieflisting.zpid)

                        if brieflistinginDB.homeStatus == 'PENDING':
                            print(brieflisting.__str__() + ' has changed from Pending to SOLD!!!')
                        elif brieflistinginDB.homeStatus == 'FOR_SALE':
                            print(brieflisting.__str__() + ' has changed from For sale to Sold!!!')

                        if brieflisting.zpid in zpidofinterest:
                            EmailCustomersIfInterested(brieflisting.zpid, brieflisting, brieflistinginDB)

                        brieflistinginDB.homeStatus = brieflisting.homeStatus
                        brieflistinginDB.soldprice = brieflisting.price
                        brieflistinginDB.price = brieflisting.price
                        brieflistinginDB.soldtime = brieflisting.soldtime
                        brieflistinginDB.getPropertyData()
                        brieflistinginDB.zone_id = zone_id

                        brieflistingcontroller.setZoneForBriefListing(brieflisting, zonepolygons)
                        brieflistingcontroller.updateBriefListing(brieflistinginDB)
                    except Exception as e:
                        print(e, brieflisting, 'Error updating sold unit')
                    continue

                try:
                    print(f"{ccc} out of {soldbrieflistingarr.__len__()}")
                    brieflisting.getPropertyData()
                    brieflisting.zone_id = zone_id
                    brieflistingcontroller.setZoneForBriefListing(brieflisting, zonepolygons)
                    newsoldbriefs.append(brieflisting)

                    if len(newsoldbriefs) > 100:
                        brieflistingcontroller.SaveBriefListingArr(newsoldbriefs)
                        newsoldbriefs = []
                except Exception as e:
                    print(e, brieflisting)

            brieflistingcontroller.SaveBriefListingArr(newsoldbriefs)
            return jsonify({
                'status': 'success',
                'message': f'Zone {zone.zonename()} sold listings updated.',
                'new_sold': len(newsoldbriefs),
                'total_processed': len(soldbrieflistingarr)
            }), 200
        except Exception as e:
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500


@maintanance_bp.route('/maintainFORSALEListingsByZone', methods=['PATCH'])
def maintainFORSALEListingsByZone():
    """
    Zone-based version of maintainFORSALEListings - more cost-efficient than city-based search
    """
    if request.method == 'PATCH':
        zone_id = int(request.form.get('zone_id'))

        zone = washingtonzonescontroller.getZonebyID(zone_id)
        zonepolygons = washingtonzonescontroller.load_zone_polygons()

        try:
            # Get for-sale listings from API using zone polygon
            forsalebrieflistingarr = []
            forsalerawdata = SearchZillowHomesByZone(zone, status="For_Sale", soldInLast="Any")
            for briefhomedata in forsalerawdata:
                forsalebrieflistingarr.append(BriefListing.CreateBriefListing(briefhomedata, None, None, zone.City))

            forsaleAPIbrief_dict = {listing.zpid: listing for listing in forsalebrieflistingarr}

            count = 0
            newsalebriefs = []

            # Get for-sale listings from DB for this zone
            for_sale_DB = BriefListing.query.filter(
                BriefListing.zone_id == zone_id,
                BriefListing.homeStatus == FOR_SALE
            ).all()
            forsaledb_ids = [brieflist.zpid for brieflist in for_sale_DB]
            zpidofinterest = customerzpidcontroller.getAllZPIDS_Customerzpids()

            for api_zpid, brieflisting in forsaleAPIbrief_dict.items():
                count += 1
                print(count)

                if api_zpid in forsaledb_ids:
                    brieflistdb = brieflistingcontroller.get_listing_by_zpid(api_zpid)
                    if brieflistdb.price != brieflisting.price:
                        print(f"Price Change for {brieflistdb}")
                        print(f"From {brieflistdb.price} to {brieflisting.price}")

                        if api_zpid in zpidofinterest:
                            EmailCustomersIfInterested(api_zpid, brieflisting, brieflistdb)

                        brieflistdb.getPropertyData()
                        brieflistdb.zone_id = zone_id
                        brieflistdb.price = brieflisting.price
                        brieflistdb.lpctime = datetime.now().timestamp()
                        brieflistingcontroller.updateBriefListing(brieflistdb)
                    continue

                try:
                    brieflisting.getPropertyData()
                    brieflisting.zone_id = zone_id
                    brieflistingcontroller.setZoneForBriefListing(brieflisting, zonepolygons)
                    newsalebriefs.append(brieflisting)

                    if len(newsalebriefs) > 10:
                        brieflistingcontroller.SaveBriefListingArr(newsalebriefs)
                        newsalebriefs = []
                except Exception as e:
                    print(e, brieflisting)

            brieflistingcontroller.SaveBriefListingArr(newsalebriefs)

            # Check for mismanaged listings (in DB but not in API)
            mismanageddict = {}
            for brieflisting in for_sale_DB:
                if brieflisting.zpid in forsaleAPIbrief_dict.keys():
                    continue
                else:
                    mismanageddict = ZPIDinDBNotInAPI_FORSALE(brieflisting.zpid, 90, mismanageddict)

            return jsonify({
                'status': 'success',
                'message': f'Zone {zone.zonename()} for-sale listings updated.',
                'new_for_sale': len(newsalebriefs),
                'total_processed': len(forsalebrieflistingarr),
                'mismanaged': len(mismanageddict)
            }), 200
        except Exception as e:
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500


@maintanance_bp.route('/maintainListingsByZone', methods=['GET'])
def maintainListingsByZone():
    """
    Legacy endpoint - use /maintainSoldListingsByZone or /maintainFORSALEListingsByZone instead
    """
    zone_id = request.form.get('zone_id')
    zone = washingtonzonescontroller.getZonebyID(zone_id)
    print(f"Zone: {zone.zonename()}, Current listings in DB: {zone.brief_listings.__len__()}")

    # Test search
    results = SearchZillowHomesByZone(zone, status="For_Sale")
    print(f"Found {len(results)} for-sale listings from API")

    return jsonify({
        'status': 'info',
        'zone': zone.zonename(),
        'db_listings': zone.brief_listings.__len__(),
        'api_results': len(results),
        'message': 'Use /maintainSoldListingsByZone or /maintainFORSALEListingsByZone for full updates'
    }), 200


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

@maintanance_bp.route('/clients_listing_Recommendation', methods=['PATCH'])
def clients_listing_Recommendation():
    customer_id = request.args.get("customer_id", type=int, default=None)
    customer = customerzonecontroller.get_customer(customer_id)

    forsalehomes = brieflistingcontroller.getListingByCustomerPreference(
        customer, FOR_SALE, 90
    ).all()

    updated_count = 0
    new_high_scoring_listings = []

    # Configuration: set to True to send alerts to clients instead of admin
    SEND_TO_CLIENT = False
    HIGH_SCORE_THRESHOLD = 70
    EXCELLENT_SCORE_THRESHOLD = 90  # For priority alerts

    # Get customer's zone interests
    customer_zone_ids = [cz.zone_id for cz in customer.zones] if customer.zones else []
    customer_zone_names = [cz.zone.zonename() for cz in customer.zones] if customer.zones else []

    # Track skipped listings for reporting
    skipped_count = 0

    for forsale_bl in forsalehomes:
        # Check if this is a new listing (never evaluated before)
        previous_eval = ailistingcontroller.get_latest_evaluation(customer_id, forsale_bl.zpid)
        is_new_listing = previous_eval is None

        # Skip if nothing changed that matters (price)
        if not ailistingcontroller.should_re_evaluate(customer_id, forsale_bl):
            continue

        propertydata = forsale_bl.getPropertyData()
        brieflistingcontroller.updateBriefListing(forsale_bl)

        # Check if listing is in customer's interested zones
        is_in_preferred_zone = forsale_bl.zone_id in customer_zone_ids if forsale_bl.zone_id else False
        listing_zone_name = forsale_bl.zone.zonename() if forsale_bl.zone else "Unknown"

        # PRE-FILTER: Skip AI evaluation if listing is NOT in preferred zone AND fails basic criteria
        if not is_in_preferred_zone and customer_zone_ids:  # Only apply zone filter if customer has zone preferences
            # Check basic price fit
            price_in_range = True
            if customer.minprice and customer.maxprice and forsale_bl.price:
                price_in_range = customer.minprice <= forsale_bl.price <= customer.maxprice

            # Check basic size fit
            size_in_range = True
            if customer.minsqft and customer.maxsqft and forsale_bl.livingArea:
                size_in_range = customer.minsqft <= forsale_bl.livingArea <= customer.maxsqft

            # Skip if both price AND size are out of range
            if not price_in_range and not size_in_range:
                skipped_count += 1
                print(f"Skipped {forsale_bl.zpid} - wrong zone + price/size mismatch")
                continue

        # Passed pre-filter, send to AI for evaluation
        ai_response = AIModel(
            forsale_bl,
            customer,
            propertydata,
            customer_zone_names=customer_zone_names,
            listing_zone_name=listing_zone_name,
            is_in_preferred_zone=is_in_preferred_zone
        )
        likelihood_score = ai_response.get("likelihood_score", 0)
        ai_comment = ai_response.get("reason", "")

        # Use BriefListing.price directly
        current_price = forsale_bl.price

        ailistingcontroller.save_ai_evaluation(
            customer_id=customer_id,
            zpid=forsale_bl.zpid,
            ai_comment=ai_comment,
            likelihood_score=likelihood_score,
            listing_price=current_price,
        )

        updated_count += 1

        # Track new high-scoring listings for email alerts
        if is_new_listing and likelihood_score >= HIGH_SCORE_THRESHOLD:
            new_high_scoring_listings.append({
                'listing': forsale_bl,
                'score': likelihood_score,
                'reason': ai_comment,
                'customer': customer
            })

    # Send email alerts for new high-scoring listings
    excellent_matches = 0
    if new_high_scoring_listings:
        from app.RouteModel.EmailModel import send_new_listing_alert
        for item in new_high_scoring_listings:
            # Check if this is an excellent match (90+)
            is_excellent = item['score'] >= EXCELLENT_SCORE_THRESHOLD
            if is_excellent:
                excellent_matches += 1

            send_new_listing_alert(
                listing=item['listing'],
                customer=item['customer'],
                score=item['score'],
                reason=item['reason'],
                send_to_client=SEND_TO_CLIENT,
                is_excellent_match=is_excellent
            )

    return {
        "Updated Recommendations": updated_count,
        "New High-Scoring Listings": len(new_high_scoring_listings),
        "Excellent Matches (90+)": excellent_matches,
        "Skipped (zone + criteria mismatch)": skipped_count
    }, 200

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
        brieflisting.getPropertyData()
        brieflistingcontroller.updateBriefListing(brieflisting)

    return {"Seattle Neighbourhood_subs updated": 'listings.__len__()'}, 200

from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
# from app.MapTools.MappingTools import citygeojson_features, WA_geojson_features


@maintanance_bp.route('/updateathing4', methods=['post'])
def updateathing4():
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    # iter_value = request.args.get('iter')
    # washingtonzonescontroller.repair_from_geojson(citygeojson_features,WA_geojson_features, washingtoncitiescontroller)
    WA_geojson_features = washingtonzonescontroller.getallGeoJson()
    washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)

    return {"Seattle Neighbourhood_subs updated": 'listings.__len__()'}, 200

from shapely.geometry import Polygon, MultiPolygon, Point
@maintanance_bp.route('/updateathing5', methods=['post'])
def updateathing5():
    # washingtonzonescontroller.update_geometry_from_geojson(WA_geojson_features)
    # iter_value = request.args.get('iter')
    zone_id = int(request.args.get('zone_id'))
    # listings = (BriefListing.query.filter(BriefListing.zone_id== zone_id)
    #  .filter(BriefListing.homeStatus == RECENTLYSOLD) .all())
    zonepolygons = washingtonzonescontroller.load_zone_polygons()
    listings = (BriefListing.query.filter(BriefListing.city=="Seattle")
                .filter(BriefListing.zone_id.is_(None)).all())

    for polygon in zonepolygons:
        cityname = None
        neighbourhood = None
        zone = 99999
        # if polygon["zone"].zonename() not in ["North Brier","Bothell North","Lynnwood North",
        #                                       "Lake Stickney",
        #                                       "Lynnwood East","East Brier","Mill Creak South"
        #                                       ,"Mill Creek East"] :
        # # if polygon["zone"].zonename() not in ["Bothell North"] :
        #     continue
        for brieflisting in listings[0:100]:
            print(brieflisting)
            oldzone = brieflisting.zone_id
            if oldzone is None:
                pause = True
            # brieflisting.getPropertyData()
            if polygon["geom"].contains(Point(brieflisting.longitude, brieflisting.latitude)):
                zone = polygon["zone"]
                cityname = zone.City
                neighbourhood = zone.neighbourhood
                brieflisting.zone_id = zone.id
                if brieflisting.zone_id != oldzone:
                    print(f"Zone being Updated! {brieflisting}")
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


@maintanance_bp.route('/repairBriefListing', methods=['POST', 'GET'])
def repairBriefListing():
    """
    Repair/refresh a BriefListing by fetching fresh data from Zillow API.

    Usage:
        POST /maintanance/repairBriefListing
        Body: {"zpid": "12345678"}

        OR

        GET /maintanance/repairBriefListing?zpid=12345678

    Returns:
        Success: {"status": "success", "message": "BriefListing repaired", "zpid": "12345678"}
        Error: {"status": "error", "message": "Error message", "zpid": "12345678"}
    """
    try:
        # Get zpid from POST body or GET query parameter
        if request.method == 'POST':
            data = request.get_json()
            zpid = data.get('zpid') if data else None
        else:  # GET
            zpid = request.args.get('zpid')

        if not zpid:
            return jsonify({
                'status': 'error',
                'message': 'zpid is required (provide via POST body or GET query parameter)'
            }), 400

        # Fetch fresh property data from Zillow API
        print(f"[REPAIR] Fetching fresh data for zpid {zpid}...")
        propertydata = SearchZillowByZPID(zpid)

        if not propertydata:
            return jsonify({
                'status': 'error',
                'message': f'Failed to fetch property data from Zillow API',
                'zpid': zpid
            }), 404

        # Create/update BriefListing using the fresh data
        print(f"[REPAIR] Updating BriefListing for zpid {zpid}...")
        brieflisting = brieflistingcontroller.CreateBriefListingFromPropertyData(propertydata)

        if not brieflisting:
            return jsonify({
                'status': 'error',
                'message': f'Failed to create BriefListing from property data',
                'zpid': zpid
            }), 500

        # Save the updated listing
        brieflistingcontroller.updateBriefListing(brieflisting)

        print(f"[REPAIR] Successfully repaired zpid {zpid}")
        return jsonify({
            'status': 'success',
            'message': f'BriefListing repaired successfully',
            'zpid': zpid,
            'address': f"{brieflisting.streetAddress}, {brieflisting.city}" if brieflisting else None
        }), 200

    except Exception as e:
        print(f"[REPAIR ERROR] Failed to repair zpid {zpid}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Repair failed: {str(e)}',
            'zpid': zpid if 'zpid' in locals() else None
        }), 500
