from app.DBModels.BriefListing import BriefListing
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief
from app.MapTools.MappingTools import findNeighbourhoodfromCoord
from app.DBModels.FSBOStatus import FSBOStatus


import os
def is_equal_with_tolerance(val1, val2, tolerance=1e-4):
    return abs(val1 - val2) <= tolerance
class BriefListingController():

    def __init__(self):
        self.db = db
        self.BriefListing = BriefListing

    def addBriefListing(self,brieflisting):
        try:
            gapis_neighbourhood = get_neighborhood(brieflisting.latitude, brieflisting.longitude)
            brieflisting.gapis_neighbourhood = gapis_neighbourhood
            brieflisting.neighbourhood = findNeighbourhoodfromCoord(brieflisting.city, brieflisting.longitude,
                                                                    brieflisting.latitude)
            brieflisting.listday = datetime.now()
            print_and_log('Adding new listing for ' + brieflisting.ref_address())
            self.db.session.add(brieflisting)
            self.db.session.commit()
        # changebrieflistingarr.append(brieflisting)
        except Exception as e:
            print_and_log(f"Error during update or insert: {str(e)}")
            self.db.session.rollback()

    def updateBriefListing(self,updatedbrieflisting, fsbo_status=None):
        try:
            print_and_log('Updating existing listing for ' + updatedbrieflisting.streetAddress)
            self.db.session.merge(updatedbrieflisting)
            # If FSBO status is provided, update it as well
            if fsbo_status:
                existing_fsbo_status = self.db.session.query(FSBOStatus).filter_by(
                    zpid=updatedbrieflisting.zpid).first()

                if existing_fsbo_status:
                    # Update FSBO status fields
                    if fsbo_status.hasContactedOnline and not existing_fsbo_status.hasContactedOnline:
                        existing_fsbo_status.hasContactedOnline = True
                        existing_fsbo_status.contactedOnlineTimestamp = datetime.utcnow()  # Set timestamp for online contact

                    if fsbo_status.hasPostCarded and not existing_fsbo_status.hasPostCarded:
                        existing_fsbo_status.hasPostCarded = True
                        existing_fsbo_status.postcardedTimestamp = datetime.utcnow()  # Set timestamp for postcard

                else:
                    # If FSBO status does not exist, add a new entry with timestamps
                    new_fsbo_status = FSBOStatus(
                        zpid=updatedbrieflisting.zpid,
                        hasContactedOnline=fsbo_status.hasContactedOnline,
                        hasPostCarded=fsbo_status.hasPostCarded,
                        contactedOnlineTimestamp=datetime.utcnow() if fsbo_status.hasContactedOnline else None,
                        postcardedTimestamp=datetime.utcnow() if fsbo_status.hasPostCarded else None
                    )
                    self.db.session.add(new_fsbo_status)


            self.db.session.commit()
        # changebrieflistingarr.append(brieflisting)
        except Exception as e:
            print_and_log(f"Error during update or insert: {str(e)}")
            self.db.session.rollback()
    def SaveBriefListingArr(self,brieflistingarr):
        changebrieflistingarr=[]
        oldbrieflistingarr=[]
        file_path = os.path.join(os.getcwd(), 'unique_neighbourhoods.txt')
        with open(file_path, 'a') as file:

            for index,brieflisting in enumerate(brieflistingarr):
                print(index)
                try:
                    # print(brieflisting.ref_address())
                    existing_listing = self.db.session.query(BriefListing).filter_by(zpid=brieflisting.zpid).first()
                    if existing_listing:
                        needs_update = False
                        updatereason=''
                        gapis_neighbourhood = get_neighborhood(brieflisting.latitude, brieflisting.longitude)
                        brieflisting.gapis_neighbourhood=gapis_neighbourhood
                        brieflisting.neighbourhood=findNeighbourhoodfromCoord(brieflisting.city,brieflisting.longitude,brieflisting.latitude)
                        # print_and_log('Updating existing listing for ' + brieflisting.streetAddress)
                        if brieflisting.neighbourhood != existing_listing.neighbourhood:
                            print('===============================Rewriting neighbourhood==============================')
                            print(existing_listing)
                            print(brieflisting)
                            needs_update = True
                            print('=============================================================')

                        for attr in vars(brieflisting):
                            if attr == '_sa_instance_state':
                                continue
                            if attr == 'daysOnZillow':
                                continue
                            if attr == 'listtime':
                                if not is_equal_with_tolerance(existing_value, new_value, 100):
                                    needs_update = True
                                    updatereason= updatereason+ ',' +  attr + ' value update'
                                    break
                                continue
                            if hasattr(existing_listing, attr):
                                existing_value = getattr(existing_listing, attr)
                                new_value = getattr(brieflisting, attr)
                                if isinstance(existing_value, decimal.Decimal) and isinstance(new_value, decimal.Decimal):
                                    # For float values, use the tolerance-based comparison
                                    if not is_equal_with_tolerance(existing_value, new_value):
                                        needs_update = True
                                        updatereason= updatereason+ ',' + attr + ' value update'
                                        break
                                elif isinstance(existing_value, float) and isinstance(new_value, float):
                                    # For float values, use the tolerance-based comparison
                                    if not is_equal_with_tolerance(existing_value, new_value, 0.1):
                                        needs_update = True
                                        updatereason= updatereason+ ',' +  attr + ' value update'
                                        break

                                elif attr=='homeStatus':
                                    if not existing_value==new_value:
                                        needs_update = True
                                        updatereason = updatereason+ ',' +  attr + 'from ' + existing_listing + ' to ' + new_value
                                elif existing_value != new_value:
                                    # For all other data types, use standard comparison
                                    needs_update = True
                                    updatereason =  updatereason+ ',' + attr + ' value update'
                                    break
                        if needs_update:
                            print_and_log('Updating existing listing for ' + brieflisting.streetAddress)
                            print_and_log(updatereason)
                            # Update all relevant fields you want to update
                            # for attr, value in vars(brieflisting).items():
                            #     if hasattr(existing_listing, attr):  # Optional: Check if the attribute should be updated
                            #         setattr(existing_listing, attr, value)
                            # Since merge is used, it will update if the primary key exists, otherwise insert.
                            self.db.session.merge(brieflisting)
                            changebrieflistingarr.append(brieflisting)
                        else:
                            oldbrieflistingarr.append(brieflisting)
                            print('No updates necessary for ' + brieflisting.streetAddress)
                            continue
                    else:
                        gapis_neighbourhood = get_neighborhood(brieflisting.latitude, brieflisting.longitude)
                        brieflisting.gapis_neighbourhood=gapis_neighbourhood
                        brieflisting.neighbourhood=findNeighbourhoodfromCoord(brieflisting.city,brieflisting.longitude,brieflisting.latitude)
                        brieflisting.listday= datetime.now()
                        print_and_log('Adding new listing for ' + brieflisting.ref_address())
                        self.db.session.add(brieflisting)
                        changebrieflistingarr.append(brieflisting)
                    print_and_log('Committing ' + brieflisting.ref_address())
                    self.db.session.commit()
                except Exception as e:
                    print_and_log(f"Error during update or insert: {str(e)}")
                    self.db.session.rollback()
        return changebrieflistingarr,oldbrieflistingarr

    def UpdateBriefListing(self,brieflisting):
        try:
            self.db.session.merge(brieflisting)
            self.db.session.commit()
        except Exception as e:
            print_and_log(f"Error during update or insert: {str(e)}")
            self.db.session.rollback()

    def listingsN_Cleanup(self):
        # Query to find all listings with 'FIX ME' as the neighborhood
        FIXMEListingsQuery = self.db.session.query(BriefListing).filter_by(neighbourhood='FIX ME')
        for fixmelisting in FIXMEListingsQuery:
            print(fixmelisting)
            fixmelisting.gapis_neighbourhood = get_neighborhood(fixmelisting.latitude, fixmelisting.longitude)
            self.db.session.merge(fixmelisting)
            print(fixmelisting.zpid)
            loadPropertyDataFromBrief(fixmelisting)
        self.db.session.commit()

        # Execute the query and count the results
        FIXMEListingsCount = FIXMEListingsQuery.count()

        # Return the count of listings needing cleanup
        return f'cleanup FIXME count {FIXMEListingsCount}'

    def ListingsByNeighbourhood(self, neighbourhood, days_ago):
        # Calculate the date for the given days ago from today
        date_threshold = datetime.now() - timedelta(days=days_ago)

        # Convert `date_threshold` to Unix timestamp in milliseconds since
        # `dateSold` is stored as Unix timestamp in milliseconds
        date_threshold_ms = date_threshold.timestamp() * 1000

        # Query the database for listings in the specified neighbourhood
        # and sold within the last `days_ago` days.
        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood == neighbourhood,
            BriefListing.dateSold >= date_threshold_ms
        ).all()

        return unfiltered_soldhomes

    def zpidsForSaleInNeighbourhood(self, neighbourhood, days_ago):
        # Calculate the date for the given days ago from today
        date_threshold = datetime.now() - timedelta(days=days_ago)

        # Convert `date_threshold` to Unix timestamp in milliseconds since
        # `dateSold` is stored as Unix timestamp in milliseconds
        date_threshold_ms = date_threshold.timestamp() * 1000

        # Query the database for listings in the specified neighbourhood
        # and sold within the last `days_ago` days.
        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood == neighbourhood,
            BriefListing.dateSold >= date_threshold_ms,
            BriefListing.homeStatus =="FOR_SALE"
        ).all()
        return [brieflisting.zpid for brieflisting in unfiltered_soldhomes]

    def get_listing_by_zpid(self, zpid):
        # Query the database for the listing with the given zpid
        listing = BriefListing.query.filter_by(zpid=zpid).first()
        return listing
    def get_listings_by_ids(self, ids):
        # Query the database for listings with the given ids
        listings = BriefListing.query.filter(BriefListing.zpid.in_(ids)).all()
        return listings

    def forSaleInNeighbourhood(self, neighbourhood, days_ago):
        # Calculate the date for the given days ago from today
        date_threshold = datetime.now() - timedelta(days=days_ago)

        date_threshold_ms = date_threshold.timestamp()

        # Query the database for listings in the specified neighbourhood
        # and sold within the last `days_ago` days.
        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood == neighbourhood,
            BriefListing.homeStatus == "FOR_SALE"
        ).all()

        # Extract the IDs from the brief listings
        # forsaleinarea_ids = [listing.zpid for listing in unfiltered_soldhomes]
        #
        # # Assuming forsalebriefarr is a list of brief listings currently on sale as extracted by the API
        # # Extract the IDs from the brief listings
        # forsalebrief_ids = [listing.zpid for listing in forsalebriefarr]
        #
        # # Finding IDs in forsaleinarea that are not in forsalebrief_ids
        # no_longer_selling_ids = [zpid for zpid in forsaleinarea_ids if zpid not in forsalebrief_ids]
        #
        # # Get the listings from the database with those IDs
        # no_longer_selling_listings = self.get_listings_by_ids(no_longer_selling_ids)

        return unfiltered_soldhomes

    def forSaleInCity(self, city):
        # Calculate the date for the given days ago from today
        # date_threshold = datetime.now() - timedelta(days=days_ago)
        #
        # date_threshold_ms = date_threshold.timestamp()

        # Query the database for listings in the specified neighbourhood
        # and sold within the last `days_ago` days.
        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.city == city,
            BriefListing.homeStatus == "FOR_SALE",
            BriefListing.homeType.in_(Config.HOMETYPES)

        ).all()

        # Extract the IDs from the brief listings
        # forsaleinarea_ids = [listing.zpid for listing in unfiltered_soldhomes]
        #
        # # Assuming forsalebriefarr is a list of brief listings currently on sale as extracted by the API
        # # Extract the IDs from the brief listings
        # forsalebrief_ids = [listing.zpid for listing in forsalebriefarr]
        #
        # # Finding IDs in forsaleinarea that are not in forsalebrief_ids
        # no_longer_selling_ids = [zpid for zpid in forsaleinarea_ids if zpid not in forsalebrief_ids]
        #
        # # Get the listings from the database with those IDs
        # no_longer_selling_listings = self.get_listings_by_ids(no_longer_selling_ids)

        return unfiltered_soldhomes

    def OpenHousePotential(self):
        openhouse_brieflistings = BriefListing.query.filter(
            BriefListing.openhouseneed == True,
            BriefListing.homeStatus == "FOR_SALE"
        ).all()
        return openhouse_brieflistings


    def uniqueNeighbourhood(self, city):
        # Calculate the date for the given days ago from today
        unique_neighbourhoods_query=BriefListing.query.with_entities(
            BriefListing.neighbourhood
        ).filter(
            BriefListing.city == city
        ).distinct().all()
        unique_neighbourhoods = [neighbourhood[0] for neighbourhood in unique_neighbourhoods_query]
        return unique_neighbourhoods

    def SoldHomesinNeighbourhood(self, neighbourhood, days_ago):
        date_threshold = datetime.now() - timedelta(days=days_ago)
        date_threshold_ms = int(date_threshold.timestamp() * 1000)

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood==neighbourhood,
            BriefListing.homeStatus == 'RECENTLY_SOLD',
            BriefListing.dateSold >= date_threshold_ms
        ).all()

        return unfiltered_soldhomes

    def ListingsByNeighbourhoodsAndHomeTypes(self, neighbourhoods, homeTypes, days_ago,homeStatus):
        date_threshold = datetime.now() - timedelta(days=days_ago)
        date_threshold_ms = int(date_threshold.timestamp() * 1000)

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood.in_(neighbourhoods),
            # BriefListing.homeType.in_(homeTypes),
            BriefListing.homeStatus == homeStatus,
            BriefListing.dateSold >= date_threshold_ms
        ).all()

        return unfiltered_soldhomes
    def ForSaleListingsByNeighbourhoodsAndHomeTypes(self, neighbourhoods, homeTypes, days_ago,homeStatus):
        date_threshold = datetime.now() - timedelta(days=days_ago)
        date_threshold_ms = int(date_threshold.timestamp() * 1000)

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood.in_(neighbourhoods),
            # BriefListing.homeType.in_(homeTypes),
            BriefListing.homeStatus == homeStatus,
        ).all()

        return unfiltered_soldhomes

    def ForSaleListingsByCitiesAndHomeTypes(self, cities, homeTypes, days_ago=365):
        date_threshold = datetime.now() - timedelta(days=days_ago)
        date_threshold_ms = int(date_threshold.timestamp() * 1000)

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.city.in_(cities),
            BriefListing.homeType.in_(homeTypes),
            BriefListing.homeStatus == 'FOR_SALE',
        ).all()

        return unfiltered_soldhomes

    def UniqueNeighbourhoodsByCities(self, cities):
        # Query the database for distinct neighbourhoods in the specified cities
        unique_neighbourhoods = BriefListing.query.with_entities(
            distinct(BriefListing.neighbourhood)
        ).filter(
            BriefListing.city.in_(cities)
        ).all()

        # Extract neighbourhoods from the query result
        neighbourhoods = [neighbourhood[0] for neighbourhood in unique_neighbourhoods]

        return neighbourhoods

    def getFSBOListings(self):
        try:
            # Query to filter listings where SoldBy is "FSBO"
            fsbo_listings = self.BriefListing.query.filter_by(soldBy='FSBO').all()
            return fsbo_listings
        except Exception as e:
            print_and_log(f"Error retrieving FSBO listings: {str(e)}")
            return []

    def UniqueCities(self):
        # Query the database for distinct neighbourhoods in the specified cities
        unique_cities = BriefListing.query.with_entities(
            distinct(BriefListing.cities)
        ).all()

        # Extract neighbourhoods from the query result
        cities = [city[0] for city in unique_cities]

        return cities

    def latestListingTime(self,city=None, neighbourhood_sub=None):
        query = BriefListing.query

        # Apply city filter if provided
        if city:
            query = query.filter(BriefListing.city == city)

        if neighbourhood_sub:
            query = query.filter(BriefListing.neighbourhood_sub == neighbourhood_sub)

        # Get the latest listtime from the filtered results
        latest_time = query.with_entities(
            func.max(BriefListing.listtime).label('latest_listtime')
        ).scalar()

        return latest_time

    def getListingsWithStatus(self, fromdays, homeStatus):  #pendingListings(self, fromdays):
        days_ago = int((datetime.now() - timedelta(days=fromdays)).timestamp())
        # Count entries with homestatus = 'PENDING' and pendday in the last 7 days
        if homeStatus == 'PENDING':
            results = BriefListing.query.filter(
                BriefListing.homeStatus == homeStatus,
                BriefListing.pendday >= days_ago
            )
        elif homeStatus == 'RECENTLY_SOLD':
            results = BriefListing.query.filter(
                BriefListing.homeStatus == homeStatus,
                BriefListing.dateSold >= days_ago
            )
        elif homeStatus == 'FOR_SALE':
            results = BriefListing.query.filter(
                BriefListing.homeStatus == homeStatus,
                BriefListing.listtime >= days_ago
            )
        elif homeStatus == 'OTHER':
            results = BriefListing.query.filter(
                BriefListing.homeStatus == homeStatus,
                BriefListing.listtime >= days_ago
            )
        else:
            results = BriefListing.query.filter(
                BriefListing.homeStatus == homeStatus,
                BriefListing.dateSold >= days_ago
            )

        return results

    def pendingListingsByCity(self, city, fromdays,  neighbourhood_sub=None, homeType=None ):
        fromdays_ago = int((datetime.now() - timedelta(days=fromdays)).timestamp())
        # Count entries with homestatus = 'PENDING' and pendday in the last 7 days
        recent_pending = BriefListing.query.filter(
            BriefListing.homeStatus == 'PENDING',
            BriefListing.city == city,
            BriefListing.pendday >= fromdays_ago
        )

        if neighbourhood_sub:
            recent_pending = recent_pending.filter(BriefListing.neighbourhood_sub == neighbourhood_sub)
        if homeType:
            if isinstance(homeType, list):
                recent_pending = recent_pending.filter(BriefListing.homeType.in_(homeType))
            else:
                recent_pending = recent_pending.filter(BriefListing.homeType == homeType)

        return recent_pending

    def soldListingsByCity(self, city, fromdays, neighbourhood_sub=None, homeType=None):
        fromdays_ago = int((datetime.now() - timedelta(days=fromdays)).timestamp())
        # Count entries with homestatus = 'PENDING' and pendday in the last 7 days
        recent_sold = BriefListing.query.filter(
            BriefListing.homeStatus == 'RECENTLY_SOLD',
            BriefListing.city == city,
            BriefListing.dateSold >= fromdays_ago*1000
        )

        if neighbourhood_sub:
            recent_sold = recent_sold.filter(BriefListing.neighbourhood_sub == neighbourhood_sub)
        if homeType:
            if isinstance(homeType, list):
                recent_sold = recent_sold.filter(BriefListing.homeType.in_(homeType))
            else:
                recent_sold = recent_sold.filter(BriefListing.homeType == homeType)

        return recent_sold

    def forSaleListingsByCity(self, city, fromdays=365, neighbourhood_sub=None, homeType=None, maxprice=None,
                              minprice=None):
        # Calculate the cutoff datetime
        fromdays_ago = datetime.now() - timedelta(days=fromdays)
        # Start with the base filters
        filters = [
            BriefListing.homeStatus == 'FOR_SALE',
            BriefListing.city == city,
            BriefListing.listtime >= fromdays_ago
        ]
        # Add optional parameters dynamically
        if neighbourhood_sub:
            filters.append(BriefListing.neighbourhood_sub == neighbourhood_sub)
        if homeType:
            filters.append(
                BriefListing.homeType.in_(homeType) if isinstance(homeType,
                                                                  list) else BriefListing.homeType == homeType)
        if maxprice:
            filters.append(BriefListing.price <= maxprice)
        if minprice:
            filters.append(BriefListing.price >= minprice)
        # Execute the query with all filters applied at once
        return BriefListing.query.filter(*filters)

    def getALLlistings(self):
        """
        Retrieve all listings from the BriefListing table.

        :return: List of BriefListing objects
        """
        try:
            all_listings = self.BriefListing.query.all()
            return all_listings
        except Exception as e:
            print(f"Error retrieving all listings: {str(e)}")
            return []

brieflistingcontroller = BriefListingController()