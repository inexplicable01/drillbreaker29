from app.DBModels.CityStatsCache import CityStatsCache
from sqlalchemy.sql import func
from app.extensions import db
from datetime import datetime, timedelta
from app.DBFunc.SeattlleNeighbourhoodsController import seattleneighbourhoodcontroller
from app.config import Config, SW
import pytz

class CityStatsCacheController:
    def __init__(self):
        self.db = db
        self.CityStatsCache = CityStatsCache

    def get_all_city_stats(self):
        """Retrieve all city statistics from the cache."""
        return self.db.session.query(self.CityStatsCache).all()

    def get_city_stats_by_name(self, city, neighbourhood_sub):
        """Retrieve city stats for a given CustomerNeighbourhoodInterest object."""
        if city == "Seattle":  # Assuming city_name is always Seattle
            if neighbourhood_sub is None:
                return self.db.session.query(self.CityStatsCache).filter_by(
                    city_name=f"{city}"
                ).first()
            else:
                return self.db.session.query(self.CityStatsCache).filter_by(
                    city_name=f"{city}_{neighbourhood_sub}"
                ).first()
        else:
            return self.db.session.query(self.CityStatsCache).filter_by(
                city_name=f"{city}"
            ).first()




    def update_city_stats(self, city_name, sold, pending,pending1,pending7_SFH,pending7_TCA,
                          forsale,forsaleadded7_SFH,forsaleadded7_TCA,
                          sold7_SFH,sold7_TCA,
                          updated_time, neighbourhood=None, neighbourhood_sub=None):
        """Update or insert a city's stats in the cache."""
        if neighbourhood_sub is None:
            city_stats = self.db.session.query(self.CityStatsCache).filter_by(city_name=city_name).first()

            if city_stats is None:
                # Create new entry
                city_stats = CityStatsCache(city_name=city_name)
        else:
            city_stats = self.db.session.query(self.CityStatsCache).filter_by(
                city_name=f"{city_name}_{neighbourhood_sub}").first()

            if city_stats is None:
                # Create new entry
                city_stats = CityStatsCache(city_name=f"{city_name}_{neighbourhood_sub}",neighbourhood_sub=neighbourhood_sub,neighbourhood=neighbourhood)

        # Update values
        city_stats.sold = sold
        city_stats.pending = pending
        city_stats.pending1 = pending1
        city_stats.pending7_SFH = pending7_SFH
        city_stats.pending7_TCA = pending7_TCA
        city_stats.forsale = forsale
        city_stats.forsaleadded7_SFH = forsaleadded7_SFH
        city_stats.forsaleadded7_TCA = forsaleadded7_TCA
        city_stats.sold7_SFH = sold7_SFH
        city_stats.sold7_TCA = sold7_TCA
        city_stats.updated_time = updated_time
        print(city_stats)
        # Add or update in the session
        self.db.session.add(city_stats)
        self.db.session.commit()

    def refresh_city_stats(self, cities, brieflistingcontroller):
        """Refresh city stats for a list of cities."""


        for city in cities:
            print(city)
            try:
                updated_time = datetime.fromtimestamp(
                    brieflistingcontroller.latestListingTime(city)
                )
            except:
                updated_time = None
            self.update_city_stats(
                city_name=city,
                sold=brieflistingcontroller.soldListingsByCity(city, 30).count(),
                pending=brieflistingcontroller.pendingListingsByCity(city, 30).count(),
                pending1=brieflistingcontroller.pendingListingsByCity(city, 1).count(),
                forsale=brieflistingcontroller.forSaleListingsByCity(city, 365).count(),

                sold7_SFH=brieflistingcontroller.soldListingsByCity(city, 7, homeType=SW.SINGLE_FAMILY).count(),
                sold7_TCA=brieflistingcontroller.soldListingsByCity(city, 7, homeType=[SW.APARTMENT, SW.TOWNHOUSE, SW.CONDO]).count(),


                pending7_SFH=brieflistingcontroller.pendingListingsByCity(city, 7, homeType=SW.SINGLE_FAMILY).count(),
                pending7_TCA=brieflistingcontroller.pendingListingsByCity(city, 7, homeType=[SW.APARTMENT, SW.TOWNHOUSE, SW.CONDO]).count(),
                # pending7_Other=brieflistingcontroller.pendingListingsByCity(city, 7).count(),

                forsaleadded7_SFH =brieflistingcontroller.forSaleListingsByCity(city, 7, homeType=SW.SINGLE_FAMILY).count(),
                forsaleadded7_TCA=brieflistingcontroller.forSaleListingsByCity(city, 7,
                                                                               homeType=[SW.APARTMENT, SW.TOWNHOUSE, SW.CONDO]).count(),
                updated_time=updated_time
            )

        for neighbourhood in seattleneighbourhoodcontroller.getlist():
            city='Seattle'
            try:
                updated_time = datetime.fromtimestamp(
                    brieflistingcontroller.latestListingTime(city, neighbourhood.neighbourhood_sub)
                )
            except:
                updated_time = None
            print(neighbourhood.neighbourhood + ", " + neighbourhood.neighbourhood_sub)
            self.update_city_stats(
                city_name=city,
                sold=brieflistingcontroller.soldListingsByCity(city, 30,
                                                               neighbourhood_sub=neighbourhood.neighbourhood_sub).count(),
                pending=brieflistingcontroller.pendingListingsByCity(city, 30,
                                                                     neighbourhood_sub=neighbourhood.neighbourhood_sub).count(),

                pending1=brieflistingcontroller.pendingListingsByCity(city, 1,
                                                                      neighbourhood_sub=neighbourhood.neighbourhood_sub).count(),
                forsale=brieflistingcontroller.forSaleListingsByCity(city, 365,
                                                                     neighbourhood_sub=neighbourhood.neighbourhood_sub).count(),

                sold7_SFH=brieflistingcontroller.soldListingsByCity(city, 7,
                                                                    neighbourhood_sub=neighbourhood.neighbourhood_sub,
                                                                    homeType=SW.SINGLE_FAMILY).count(),
                sold7_TCA=brieflistingcontroller.soldListingsByCity(city, 7,
                                                                    neighbourhood_sub=neighbourhood.neighbourhood_sub,
                                                                    homeType=[SW.APARTMENT, SW.TOWNHOUSE,
                                                                                       SW.CONDO]).count(),

                pending7_SFH=brieflistingcontroller.pendingListingsByCity(city, 7,
                                                                          neighbourhood_sub=neighbourhood.neighbourhood_sub,
                                                                          homeType=SW.SINGLE_FAMILY).count(),
                pending7_TCA=brieflistingcontroller.pendingListingsByCity(city, 7,
                                                                          neighbourhood_sub=neighbourhood.neighbourhood_sub,
                                                                          homeType=[SW.APARTMENT, SW.TOWNHOUSE,
                                                                                             SW.CONDO]).count(),
                # pending7_Other=brieflistingcontroller.pendingListingsByCity(city, 7).count(),

                forsaleadded7_SFH=brieflistingcontroller.forSaleListingsByCity(city, 7,
                                                                               neighbourhood_sub=neighbourhood.neighbourhood_sub,
                                                                               homeType=SW.SINGLE_FAMILY).count(),
                forsaleadded7_TCA=brieflistingcontroller.forSaleListingsByCity(city, 7,
                                                                               neighbourhood_sub=neighbourhood.neighbourhood_sub,
                                                                               homeType=[SW.APARTMENT, SW.TOWNHOUSE,
                                                                                         SW.CONDO]).count(),


                updated_time=updated_time,
                neighbourhood=neighbourhood.neighbourhood,
                neighbourhood_sub=neighbourhood.neighbourhood_sub
            )


citystatscachecontroller = CityStatsCacheController()
