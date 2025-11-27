from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime, BigInteger, Text, Numeric, JSON
from app.extensions import db
from datetime import datetime

Base = declarative_base()


class SellerPropertyAnalysis(db.Model):
    """
    Stores weekly regression analysis results for Level 2 sellers.
    Tracks property value estimates based on comparable sales within 2-mile radius.
    """
    __tablename__ = 'SellerPropertyAnalysis'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)

    # Analysis metadata
    analysis_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    seller_address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(Numeric(precision=10, scale=7), nullable=True)
    longitude = db.Column(Numeric(precision=10, scale=7), nullable=True)
    property_type = db.Column(db.String(100), nullable=True)  # SINGLE_FAMILY, TOWNHOUSE, etc.

    # Comps analysis
    num_comps = db.Column(db.Integer, nullable=True)  # Number of comparable properties found
    comp_zpids = db.Column(JSON, nullable=True)  # List of ZPIDs used as comps

    # Regression results
    predicted_price = db.Column(db.BigInteger, nullable=True)  # Model's predicted price
    price_per_sqft = db.Column(db.Float, nullable=True)  # $/sqft estimate
    confidence_lower = db.Column(db.BigInteger, nullable=True)  # 95% CI lower bound
    confidence_upper = db.Column(db.BigInteger, nullable=True)  # 95% CI upper bound
    r_squared = db.Column(db.Float, nullable=True)  # Model fit quality (0-1)

    # Market stats from comps
    median_comp_price = db.Column(db.BigInteger, nullable=True)
    avg_comp_sqft = db.Column(db.Float, nullable=True)
    avg_days_on_market = db.Column(db.Integer, nullable=True)
    median_price_per_sqft = db.Column(db.Float, nullable=True)

    # Trend tracking
    week_over_week_change_pct = db.Column(db.Float, nullable=True)  # % change from last week
    week_over_week_change_dollars = db.Column(db.Integer, nullable=True)  # $ change from last week

    # Additional metadata
    model_features = db.Column(JSON, nullable=True)  # Features used in regression (sqft, beds, baths, etc.)
    notes = db.Column(Text, nullable=True)  # Any special notes or warnings

    def __repr__(self):
        return f"<SellerPropertyAnalysis {self.id}: Customer {self.customer_id}, ${self.predicted_price:,} on {self.analysis_date.strftime('%Y-%m-%d')}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'seller_address': self.seller_address,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'property_type': self.property_type,
            'num_comps': self.num_comps,
            'predicted_price': self.predicted_price,
            'price_per_sqft': self.price_per_sqft,
            'confidence_lower': self.confidence_lower,
            'confidence_upper': self.confidence_upper,
            'r_squared': self.r_squared,
            'median_comp_price': self.median_comp_price,
            'avg_comp_sqft': self.avg_comp_sqft,
            'avg_days_on_market': self.avg_days_on_market,
            'median_price_per_sqft': self.median_price_per_sqft,
            'week_over_week_change_pct': self.week_over_week_change_pct,
            'week_over_week_change_dollars': self.week_over_week_change_dollars,
            'model_features': self.model_features,
            'notes': self.notes
        }

    def get_trend_direction(self):
        """Returns 'up', 'down', or 'stable' based on week-over-week change"""
        if self.week_over_week_change_pct is None:
            return 'unknown'
        elif self.week_over_week_change_pct > 1.0:  # More than 1% increase
            return 'up'
        elif self.week_over_week_change_pct < -1.0:  # More than 1% decrease
            return 'down'
        else:
            return 'stable'