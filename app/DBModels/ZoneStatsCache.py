from app.extensions import db

class ZoneStatsCache(db.Model):
    __tablename__ = 'ZoneStatsCache'

    city_name = db.Column(db.String(255), primary_key=True)  # City name as primary key
    sold = db.Column(db.Integer, nullable=True)  # Number of sold listings
    sold7_SFH = db.Column(db.Integer, nullable=True)  # Number of sold listings
    sold7_TCA = db.Column(db.Integer, nullable=True)  # Number of sold listings
    # sold7_Other = db.Column(db.Integer, nullable=True)  # Number of sold listings
    pending = db.Column(db.Integer, nullable=True)  # Number of pending listings
    pending1 = db.Column(db.Integer, nullable=True)  # Number of pending listings
    pending7_SFH = db.Column(db.Integer, nullable=True)  # Number of pending listings
    pending7_TCA = db.Column(db.Integer, nullable=True)  # Number of pending listings
    # pending7_Other = db.Column(db.Integer, nullable=True)  # Number of pending listings
    forsale = db.Column(db.Integer, nullable=True)  # Number of listings for sale
    forsaleadded7_SFH = db.Column(db.Integer, nullable=True)  # Number of listings for sale
    forsaleadded7_TCA = db.Column(db.Integer, nullable=True)  # Number of listings for sale
    # forsaleadded7_Other = db.Column(db.Integer, nullable=True)  # Number of listings for sale

    updated_time = db.Column(db.DateTime, nullable=True)  # Last updated timestamp
    neighbourhood = db.Column(db.String(50), nullable=True)  # City name as primary key
    neighbourhood_sub = db.Column(db.String(50),nullable=True)  # Number of sold listings

    def __repr__(self):
        return (f"<ZoneStatsCache(city_name={self.city_name}, sold={self.sold}, pending={self.pending}, "
                f"pending7_SFH={self.pending7_SFH},"
                f"pending7_TCA={self.pending7_TCA},"
                f""
                f""
                f""
                f" pending1={self.pending1}, forsale={self.forsale}, updated_time={self.updated_time})>")
