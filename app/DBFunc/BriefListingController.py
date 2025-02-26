from app.DBModels.BriefListing import BriefListing
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config , RECENTLYSOLD,FOR_SALE, PENDING
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief
from app.MapTools.MappingTools import findNeighbourhoodfromCoord, get_zone_as_array
from app.DBModels.FSBOStatus import FSBOStatus
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID
import traceback
from app.MapTools.MappingTools import get_zone
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller

import os


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

    def CreateBriefListingFromPropertyData(self,propertydata):
        try:
            gapis_neighbourhood = get_neighborhood(propertydata['latitude'], propertydata['longitude'])

            neighbourhood = findNeighbourhoodfromCoord(gapis_neighbourhood.city, propertydata['latitude'],
                                                                    propertydata['longitude'])
        except Exception as e:
            gapis_neighbourhood = None
            neighbourhood = None

        return BriefListing.CreateBriefListingFromPropertyData(propertydata,neighbourhood,gapis_neighbourhood,None)

    def updateBriefListing(self,updatedbrieflisting:BriefListing, fsbo_status=None):
        ##METHOD WORKS EVEN IF upddatedbrieflisting does not exist in db yet.
        try:
            print_and_log(f'Updating existing listing for { updatedbrieflisting.streetAddress} ,{ updatedbrieflisting.city}, {updatedbrieflisting.NWMLS_id}' )
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

        for index,brieflisting in enumerate(brieflistingarr):
            print(index)
            try:
                # print(brieflisting.ref_address())
                existing_listing = self.db.session.query(BriefListing).filter_by(zpid=brieflisting.zpid).first()
                if existing_listing:

                    needs_update, updatereason = existing_listing.needsUpdate(newBrieflisting=brieflisting)

                    if needs_update:
                        print_and_log('Updating existing listing for ' + brieflisting.streetAddress)
                        print_and_log(updatereason)

                        self.db.session.merge(brieflisting)
                        changebrieflistingarr.append(brieflisting)

                    else:
                        oldbrieflistingarr.append(brieflisting)
                        print('No updates necessary for ' + brieflisting.streetAddress)
                        continue
                else:
                    gapis_neighbourhood = get_neighborhood(brieflisting.latitude, brieflisting.longitude)
                    brieflisting.gapis_neighbourhood=gapis_neighbourhood
                    # brieflisting.neighbourhood=findNeighbourhoodfromCoord(brieflisting.city,brieflisting.longitude,brieflisting.latitude)
                    brieflisting.listday= datetime.now()
                    print_and_log('Adding new listing for ' + brieflisting.ref_address())
                    self.db.session.add(brieflisting)
                    changebrieflistingarr.append(brieflisting)
                print_and_log('Committing ' + brieflisting.ref_address())
                self.db.session.commit()
            except Exception as e:
                print_and_log(f"Error during update or insert: {str(e)}")
                print_and_log("Traceback details:")
                print_and_log(traceback.format_exc())  # Outputs the full stack trace as a string
                self.db.session.rollback()
        return changebrieflistingarr,oldbrieflistingarr

    def simplebrieflistinglistupdate(self,brieflistinglist):
        for brieflisting in brieflistinglist:
            self.db.session.merge(brieflisting)
        self.db.session.commit()

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

    def get_listing_by_zpid(self, zpid):
        # Query the database for the listing with the given zpid
        listing = BriefListing.query.filter_by(zpid=zpid).first()
        return listing

    def get_listings_by_ids(self, ids):
        # Query the database for listings with the given ids
        listings = BriefListing.query.filter(BriefListing.zpid.in_(ids)).all()
        return listings

    def get_listing_by_mls_id(self, NWMLS_id):
        # Query the database for the listing with the given zpid
        listing = BriefListing.query.filter_by(NWMLS_id=NWMLS_id).first()
        return listing


    def forSaleInSearchNeigh(self, search_neigh):

        unfiltered = BriefListing.query.filter(
            BriefListing.search_neigh == search_neigh,
            BriefListing.homeStatus == "FOR_SALE",
            BriefListing.homeType.in_(Config.HOMETYPES)

        ).all()

        return unfiltered

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
        date_threshold = int((datetime.now() - timedelta(days=days_ago)).timestamp())

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood==neighbourhood,
            BriefListing.homeStatus == 'RECENTLY_SOLD',
            BriefListing.soldtime >= date_threshold
        ).all()

        return unfiltered_soldhomes

    def SoldHomesinSearch_Neigh(self, search_neigh, days_ago):
        date_threshold = int((datetime.now() - timedelta(days=days_ago)).timestamp())

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.search_neigh==search_neigh,
            BriefListing.homeStatus == 'RECENTLY_SOLD',
            BriefListing.soldtime >= date_threshold
        ).all()

        return unfiltered_soldhomes

    def ListingsByNeighbourhoodsAndHomeTypes(self, neighbourhoods, homeTypes, days_ago,homeStatus):
        date_threshold = int((datetime.now() - timedelta(days=days_ago)).timestamp())
        # date_threshold_ms = int(date_threshold.timestamp() * 1000)

        unfiltered_soldhomes = BriefListing.query.filter(
            BriefListing.neighbourhood.in_(neighbourhoods),
            # BriefListing.homeType.in_(homeTypes),
            BriefListing.homeStatus == homeStatus,
            BriefListing.soldtime >= date_threshold
        ).all()

        return unfiltered_soldhomes
    def ForSaleListingsByNeighbourhoodsAndHomeTypes(self, neighbourhoods, homeTypes, days_ago,homeStatus):
        date_threshold = int((datetime.now() - timedelta(days=days_ago)).timestamp())
        # date_threshold_ms = int(date_threshold.timestamp() * 1000)

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

    def latestListingTime(self,zone=None):
        query = BriefListing.query

        # Apply city filter if provided
        if zone:
            query = query.filter(BriefListing.zone_id == zone.id)

        # Get the latest listtime from the filtered results
        latest_time = query.with_entities(
            func.max(BriefListing.listtime).label('latest_listtime')
        ).scalar()

        return latest_time

    def setZoneForBriefListing(self,brieflisting:BriefListing):
        try:
            cityname, neighbourhood = get_zone(brieflisting.latitude, brieflisting.longitude, brieflisting.city)
            if cityname is None and neighbourhood is None:
                brieflisting.outsideZones = True
                brieflisting.zone_id = None
                return
            zone = washingtonzonescontroller.get_zone_id_by_name(cityname, neighbourhood)
            print(zone)
            if zone:
                brieflisting.zone_id = zone.id
                brieflisting.outsideZones = False
            else:
                print(zone)
        except Exception as e:
            print(e, brieflisting)
            print(brieflisting.latitude, brieflisting.longitude)
            print(brieflisting.__str__())

    def setZoneForBriefListingList(self,brieflistinglist):
        try:
            get_zone_as_array(brieflistinglist, washingtonzonescontroller)
            self.simplebrieflistinglistupdate(brieflistinglist)

        except Exception as e:
            print(e)

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
                BriefListing.soldtime >= days_ago
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
                BriefListing.soldtime >= days_ago
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
            BriefListing.soldtime >= fromdays_ago
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

    # +++++++++++++++++ZoneStarts
    def listingsByZoneandStatus(self, zone, homeStatus, fromdays, homeType=None, maxprice=None,
                              minprice=None ):
        fromdays_ago = int((datetime.now() - timedelta(days=fromdays)).timestamp())
        # Count entries with homestatus = 'PENDING' and pendday in the last 7 days

        filters = [
            BriefListing.homeStatus == homeStatus,
            BriefListing.zone_id == zone.id,
        ]
        if homeStatus== RECENTLYSOLD:
            filters.append(BriefListing.soldtime >= fromdays_ago)
        elif homeStatus== FOR_SALE:
            filters.append(BriefListing.listtime >= fromdays_ago)
        elif homeStatus==PENDING:
            filters.append(BriefListing.pendday >= fromdays_ago)
        # Add optional parameters dynamically
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

    def listingsByZonesandStatus(self, zones, homeStatus, fromdays, homeType=None, maxprice=None,
                              minprice=None ):
        fromdays_ago = int((datetime.now() - timedelta(days=fromdays)).timestamp())
        # Count entries with homestatus = 'PENDING' and pendday in the last 7 days

        filters = [
            BriefListing.homeStatus == homeStatus,
            BriefListing.zone_id.in_(zones)
        ]
        if homeStatus== RECENTLYSOLD:
            filters.append(BriefListing.soldtime >= fromdays_ago)
        elif homeStatus== FOR_SALE:
            filters.append(BriefListing.listtime >= fromdays_ago)
        elif homeStatus==PENDING:
            filters.append(BriefListing.pendday >= fromdays_ago)
        # Add optional parameters dynamically
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

# +++++++++++++++++ZoneEnds
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

    def hasListingChanged(self, brieflisting:BriefListing):
        pricechanged = False
        homestatuschanged = False
        propertyData = SearchZillowByZPID(brieflisting.zpid)
        title = f'{brieflisting.__str__()} has changed.'
        message=''
        if propertyData['price']!=brieflisting.price:
            pricechanged = True
            message+=f'Price Went {brieflisting.price} to {propertyData["price"]}\n'
        if propertyData['homeStatus']!= brieflisting.homeStatus:
            homestatuschanged = True
            message+=f'Home Status Went {brieflisting.homeStatus} to {propertyData["homeStatus"]}\n'
        return pricechanged,homestatuschanged, message, title

    def getListingByCustomerPreference(self, customer, homeStatus, fromdays, priceleeway=50000):

        fromdays_ago = int((datetime.now() - timedelta(days=fromdays)).timestamp())
        # Count entries with homestatus = 'PENDING' and pendday in the last 7 days
        filters = [
            BriefListing.homeStatus == homeStatus]

        customer_zone_ids = [zone.zone.id for zone in customer.zones]  # Extract zone IDs
        if customer_zone_ids:
            filters.append(BriefListing.zone_id.in_(customer_zone_ids))

        if homeStatus== RECENTLYSOLD:
            filters.append(BriefListing.soldtime >= fromdays_ago)
        elif homeStatus== FOR_SALE:
            filters.append(BriefListing.listtime >= fromdays_ago)
        elif homeStatus==PENDING:
            filters.append(BriefListing.pendday >= fromdays_ago)
        # Add optional parameters dynamically

        property_types= [ptype.name for ptype in customer.property_types]

        # Apply filters correctly
        if property_types:  # Only add filter if there's at least one property type
            filters.append(BriefListing.homeType.in_(property_types))

        if customer.maxprice:
            filters.append(BriefListing.price <= (customer.maxprice+priceleeway))
        if customer.minprice:
            filters.append(BriefListing.price >= (customer.minprice-priceleeway))
        # Execute the query with all filters applied at once
        return BriefListing.query.filter(*filters)




    def getFirstTenListingsWhereMLSisNull(self):
        """
        Retrieve the first ten listings from the BriefListing table where NWMLS_id is NULL.

        :return: List of the first ten BriefListing objects with NWMLS_id = NULL
        """
        try:
            first_ten_listings = (self.BriefListing.query.filter(self.BriefListing.NWMLS_id == None)
                                  .filter(self.BriefListing.soldtime > 1730400000)
                                  .all())
            return first_ten_listings
        except Exception as e:
            print(f"Error retrieving the first ten listings where NWMLS_id is null: {str(e)}")
            return []

    def getFirstXListingsWhereZoneisNull(self,X, citylist):
        """
        Retrieve the first ten listings from the BriefListing table where zone_id is NULL
        and where soldtime is greater than 1730400000.

        :return: List of the first ten BriefListing objects with zone_id = NULL
        """
        fromdays_ago = int((datetime.now() - timedelta(days=60)).timestamp())
        try:
            # Query for listings where zone_id is NULL and dateSold is greater than 1730400000000,'Bellevue','Shoreline','Bothell','Redmond','Kenmore'
            first_ten_listings = (self.BriefListing.query
                                  .filter(self.BriefListing.search_neigh.in_(citylist ) )
                                  .filter(self.BriefListing.homeStatus == RECENTLYSOLD)
                                  # .filter(self.BriefListing.city==1)
                                  # .filter(self.BriefListing.pricedelta== 0)
                                  .filter(self.BriefListing.soldtime > fromdays_ago)
                                  .limit(X)  # Limit to 10 instead of 100
                                  .all())
            return first_ten_listings
        except Exception as e:
            # Exception handling with proper error formatting
            print(f"Error retrieving the first ten listings where zone_id is NULL: {str(e)}")
            return []

    def getallPendings(self):

        try:
            # Query for listings where zone_id is NULL and dateSold is greater than 1730400000000
            first_ten_listings = (self.BriefListing.query
                                  .filter(self.BriefListing.homeStatus == PENDING)
                                  # .limit(X)  # Limit to 10 instead of 100
                                  .all())
            return first_ten_listings
        except Exception as e:
            # Exception handling with proper error formatting
            print(f"Error retrieving the first ten listings where zone_id is NULL: {str(e)}")
            return []

brieflistingcontroller = BriefListingController()