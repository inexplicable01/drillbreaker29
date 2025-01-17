from app.DBModels.CityStatsCache import CityStatsCache
from sqlalchemy.sql import func
from app.extensions import db
from datetime import datetime, timedelta
from app.config import Config
import pytz

class CityStatsCacheController:
    def __init__(self):
        self.db = db
        self.CityStatsCache = CityStatsCache

    def get_all_city_stats(self):
        """Retrieve all city statistics from the cache."""
        return self.db.session.query(self.CityStatsCache).all()

    def update_city_stats(self, city_name, sold, pending,pending1,pending7, forsale, updated_time):
        """Update or insert a city's stats in the cache."""
        city_stats = self.db.session.query(self.CityStatsCache).filter_by(city_name=city_name).first()

        if city_stats is None:
            # Create new entry
            city_stats = CityStatsCache(city_name=city_name)

        # Update values
        city_stats.sold = sold
        city_stats.pending = pending
        city_stats.pending1 = pending1
        city_stats.pending7 = pending7
        city_stats.forsale = forsale
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
                pending7=brieflistingcontroller.pendingListingsByCity(city, 7).count(),
                pending1=brieflistingcontroller.pendingListingsByCity(city, 1).count(),
                forsale=brieflistingcontroller.forSaleListingsByCity(city, 365).count(),
                updated_time=updated_time
            )


citystatscachecontroller = CityStatsCacheController()
