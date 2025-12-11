from sqlalchemy.sql import func
from sqlalchemy.orm import aliased, joinedload
from app.extensions import db
# # from app.DB
# from datetime import datetime, timedelta
# from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
# from app.config import Config, SW
# import pytz

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from app.extensions import db
from datetime import datetime


class AIListingComments(db.Model):
    __tablename__ = 'AI_Listing_Comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id', ondelete="CASCADE"), nullable=False)
    listing_id = db.Column(db.BigInteger, db.ForeignKey('BriefListing.zpid', ondelete="CASCADE"), nullable=False)

    ai_comment = db.Column(db.Text, nullable=False)
    likelihood_score = db.Column(db.Integer, nullable=False)
    listing_price = db.Column(db.Integer, nullable=True)  # NEW: price at time of evaluation

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', backref='ai_comments', lazy=True)
    listing = db.relationship('BriefListing', backref='ai_comments', lazy=True)

from sqlalchemy.sql import func
from app.extensions import db


class AIListingController:
    def __init__(self):
        self.db = db
        self.AIListingComments = AIListingComments

    @staticmethod
    def get_latest_evaluation(customer_id, zpid):
        return (
            AIListingComments.query
            .filter_by(customer_id=customer_id, listing_id=zpid)
            .order_by(AIListingComments.created_at.desc())
            .first()
        )

    @staticmethod
    def should_re_evaluate(customer_id, listing):
        """
        Re-evaluate if:
        - never evaluated before; or
        - price has changed since last eval.
        """
        latest = AIListingController.get_latest_evaluation(customer_id, listing.zpid)
        if latest is None:
            return True

        current_price = listing.price  # <--- using BriefListing.price directly

        if latest.listing_price != current_price:
            return True

        # Optional: also refresh if too old
        # if latest.created_at < datetime.utcnow() - timedelta(days=7):
        #     return True

        return False

    @staticmethod
    def save_ai_evaluation(customer_id, zpid, ai_comment, likelihood_score, listing_price=None):
        new_ai_comment = AIListingComments(
            customer_id=customer_id,
            listing_id=zpid,
            ai_comment=ai_comment,
            likelihood_score=likelihood_score,
            listing_price=listing_price,
        )
        db.session.add(new_ai_comment)
        db.session.commit()

    def retrieve_ai_evaluation(self, customer_id):
        latest_subquery = (
            self.db.session.query(
                self.AIListingComments.listing_id,
                func.max(self.AIListingComments.created_at).label("latest_created_at")
            )
            .filter(self.AIListingComments.customer_id == customer_id)
            .group_by(self.AIListingComments.listing_id)
            .subquery()
        )

        latest_evaluations = (
            self.db.session.query(self.AIListingComments)
            .join(
                latest_subquery,
                (self.AIListingComments.listing_id == latest_subquery.c.listing_id) &
                (self.AIListingComments.created_at == latest_subquery.c.latest_created_at)
            )
            .filter(self.AIListingComments.customer_id == customer_id)
            .options(joinedload(self.AIListingComments.listing))  # Eager load listing to avoid N+1
            .order_by(self.AIListingComments.likelihood_score.desc())
            .all()
        )

        return latest_evaluations


ailistingcontroller = AIListingController()
