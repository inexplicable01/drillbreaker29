from app.DBModels.ZillowBriefHomeData import BriefListing
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief


def is_equal_with_tolerance(val1, val2, tolerance=1e-4):
    return abs(val1 - val2) <= tolerance
class BriefListingController():

    def __init__(self):
        self.db = db
        self.BriefListing = BriefListing

    def SaveBriefListingArr(self,brieflistingarr):
        changebrieflistingarr=[]
        oldbrieflistingarr=[]
        for brieflisting in brieflistingarr:

            try:
                # print(brieflisting.ref_address())
                existing_listing = self.db.session.query(BriefListing).filter_by(zpid=brieflisting.zpid).first()
                if existing_listing:
                    needs_update = False

                    gapis_neighbourhood = get_neighborhood(brieflisting.latitude, brieflisting.longitude)
                    brieflisting.gapis_neighbourhood=gapis_neighbourhood
                    if gapis_neighbourhood in Config.SEATTLE_GAPIS_TO_NEIGH.keys():
                        neighbourhood=Config.SEATTLE_GAPIS_TO_NEIGH[gapis_neighbourhood]
                    else:
                        if brieflisting.city=='Maple Valley':
                            neighbourhood='Maple Valley'
                        # warnings.warn('missing neighbourhood')
                        else:
                            print('FIX ME ', gapis_neighbourhood)
                            neighbourhood='FIX ME'
                    brieflisting.neighbourhood=neighbourhood
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
                        if hasattr(existing_listing, attr):
                            existing_value = getattr(existing_listing, attr)
                            new_value = getattr(brieflisting, attr)
                            if isinstance(existing_value, decimal.Decimal) and isinstance(new_value, decimal.Decimal):
                                # For float values, use the tolerance-based comparison
                                if not is_equal_with_tolerance(existing_value, new_value):
                                    needs_update = True
                                    break
                            elif isinstance(existing_value, float) and isinstance(new_value, float):
                                # For float values, use the tolerance-based comparison
                                if not is_equal_with_tolerance(existing_value, new_value, 0.1):
                                    needs_update = True
                                    break
                            elif existing_value != new_value:
                                # For all other data types, use standard comparison
                                needs_update = True
                                break
                    if needs_update:
                        print_and_log('Updating existing listing for ' + brieflisting.streetAddress)
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
                else:
                    gapis_neighbourhood = get_neighborhood(brieflisting.latitude, brieflisting.longitude)
                    brieflisting.gapis_neighbourhood=gapis_neighbourhood
                    if gapis_neighbourhood in Config.SEATTLE_GAPIS_TO_NEIGH.keys():
                        neighbourhood=Config.SEATTLE_GAPIS_TO_NEIGH[gapis_neighbourhood]
                    else:
                        if brieflisting.city=='Maple Valley':
                            neighbourhood='Maple Valley'
                        # warnings.warn('missing neighbourhood')
                        else:
                            print('FIX ME ', gapis_neighbourhood)
                            neighbourhood='FIX ME'
                    brieflisting.neighbourhood=neighbourhood
                    print_and_log('Adding new listing for ' + brieflisting.ref_address())
                    self.db.session.add(brieflisting)
                    changebrieflistingarr.append(brieflisting)
                print_and_log('Committing ' + brieflisting.ref_address())
                self.db.session.commit()
            except Exception as e:
                print_and_log(f"Error during update or insert: {str(e)}")
                self.db.session.rollback()
        return changebrieflistingarr,oldbrieflistingarr

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

brieflistingcontroller = BriefListingController()