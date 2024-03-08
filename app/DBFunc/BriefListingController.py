from app.DBModels.ZillowBriefHomeData import BriefListing
from sqlalchemy.sql import func, or_
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
class BriefListingController():

    def __init__(self):
        self.db = db
        self.BriefListing = BriefListing

    def SaveBriefListingArr(self,brieflistingarr):
        for brieflisting in brieflistingarr:
            try:
                existing_listing = self.db.session.query(BriefListing).filter_by(zpid=brieflisting.zpid).first()
                if existing_listing:
                    print_and_log('Updating existing listing for ' + brieflisting.streetAddress)
                    # # Update all relevant fields
                    # for attr, value in vars(brieflisting).items():
                    #     setattr(existing_listing, attr, value)
                    self.db.session.merge(brieflisting)
                else:
                    print_and_log('Adding new listing for ' + brieflisting.streetAddress)
                    self.db.session.add(brieflisting)

                print_and_log('Committing ' + brieflisting.streetAddress)
                self.db.session.commit()
            except Exception as e:
                print_and_log(f"Error during update or insert: {str(e)}")
                self.db.session.rollback()

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

brieflistingcontroller = BriefListingController()