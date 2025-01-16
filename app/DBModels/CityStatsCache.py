from app.extensions import db

class CityStatsCache(db.Model):
    __tablename__ = 'CityStatsCache'

    city_name = db.Column(db.String(255), primary_key=True)  # City name as primary key
    sold = db.Column(db.Integer, nullable=True)  # Number of sold listings
    pending = db.Column(db.Integer, nullable=True)  # Number of pending listings
    pending1 = db.Column(db.Integer, nullable=True)  # Number of pending listings
    pending7 = db.Column(db.Integer, nullable=True)  # Number of pending listings
    forsale = db.Column(db.Integer, nullable=True)  # Number of listings for sale
    updated_time = db.Column(db.DateTime, nullable=True)  # Last updated timestamp

    def __repr__(self):
        return (f"<CityStatsCache(city_name={self.city_name}, sold={self.sold}, pending={self.pending}, "
                f"pending7={self.pending7}, pending1={self.pending1}, forsale={self.forsale}, updated_time={self.updated_time})>")
