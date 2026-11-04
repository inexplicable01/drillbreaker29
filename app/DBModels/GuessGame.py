import json
from datetime import datetime

from app.extensions import db


class GameListing(db.Model):
    __tablename__ = 'game_listings'

    id = db.Column(db.Integer, primary_key=True)
    zpid = db.Column(db.BigInteger, unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    list_price = db.Column(db.BigInteger, nullable=True)
    pending_date = db.Column(db.Date, nullable=True)
    listing_history = db.Column(db.Text, nullable=True)  # Zillow priceHistory as returned (JSON), newest first
    beds = db.Column(db.Float, nullable=True)
    baths = db.Column(db.Float, nullable=True)
    sqft = db.Column(db.Integer, nullable=True)
    photo_urls = db.Column(db.Text, nullable=True)  # JSON list
    zillow_url = db.Column(db.String(512), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='open')  # open, sold, expired
    final_price = db.Column(db.BigInteger, nullable=True)
    sold_date = db.Column(db.Date, nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    scored_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    guesses = db.relationship('GameGuess', backref='listing', lazy='dynamic')

    @property
    def photos(self):
        try:
            return json.loads(self.photo_urls or '[]')
        except ValueError:
            return []

    @property
    def is_open(self):
        return self.status == 'open'

    def days_pending(self, today=None):
        if not self.pending_date:
            return None
        return ((today or datetime.utcnow().date()) - self.pending_date).days

    @property
    def history(self):
        try:
            return json.loads(self.listing_history or '[]')
        except ValueError:
            return []

    def __repr__(self):
        return f"<GameListing {self.id} {self.address} {self.status}>"


class GameGuess(db.Model):
    __tablename__ = 'game_guesses'
    __table_args__ = (db.UniqueConstraint('listing_id', 'email', name='uq_game_guess_listing_email'),)

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('game_listings.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)  # stored lower-case
    guessed_price = db.Column(db.BigInteger, nullable=False)
    instagram = db.Column(db.String(64), nullable=True)
    error = db.Column(db.BigInteger, nullable=True)  # abs(guess - final_price), set when scored
    rank = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class GameRun(db.Model):
    __tablename__ = 'game_runs'

    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='running')  # running, success, failed
    picks = db.Column(db.Integer, default=0)
    checked = db.Column(db.Integer, default=0)
    scored = db.Column(db.Integer, default=0)
    expired = db.Column(db.Integer, default=0)
    api_calls = db.Column(db.Integer, default=0)
    message = db.Column(db.Text, nullable=True)
