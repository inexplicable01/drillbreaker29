from app.DBModels.AIListingComments import AIListingComments

from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from app.extensions import db
# # from app.DB
# from datetime import datetime, timedelta
# from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
# from app.config import Config, SW
# import pytz

class AIListingController:
    def __init__(self):
        self.db = db
        self.AIListingComments = AIListingComments

    @staticmethod
    def check_existing_evaluation(customer_id, zpid)->[AIListingComments]:
        """
        Checks if AI has already evaluated this listing for this customer.
        """
        existing_comment = AIListingComments.query.filter_by(
            customer_id=customer_id, listing_id=zpid
        ).first()
        return existing_comment

    @staticmethod
    def save_ai_evaluation(customer_id, zpid, ai_comment,likelihood_score):
        """
        Saves the AI evaluation result (likelihood score & comment) in the database.
        Also updates the `BriefListing` with the likelihood score.
        """

        # Save AI evaluation in AI_Listing_Comments
        new_ai_comment = AIListingComments(
            customer_id=customer_id,
            listing_id=zpid,
            ai_comment=ai_comment,
            likelihood_score=likelihood_score
        )
        db.session.add(new_ai_comment)

        # Update BriefListing to store likelihood score
        db.session.commit()

    def retrieve_ai_evaluation(self, customer_id):
        """
        Retrieves the latest AI evaluation (based on created_at) for each listing_id
        of a given customer, ordered by highest likelihood_score.
        """

        # Subquery: Get the latest created_at timestamp per listing_id
        latest_subquery = (
            self.db.session.query(
                self.AIListingComments.listing_id,
                func.max(self.AIListingComments.created_at).label("latest_created_at")
            )
            .filter(self.AIListingComments.customer_id == customer_id)
            .group_by(self.AIListingComments.listing_id)
            .subquery()
        )

        # Main query: Join back to AIListingComments to get full records
        latest_evaluations = (
            self.db.session.query(self.AIListingComments)
            .join(
                latest_subquery,
                (self.AIListingComments.listing_id == latest_subquery.c.listing_id) &
                (self.AIListingComments.created_at == latest_subquery.c.latest_created_at)
            )
            .filter(self.AIListingComments.customer_id == customer_id)
            .order_by(self.AIListingComments.likelihood_score.desc())  # Order by highest likelihood score
            .all()
        )

        return latest_evaluations


ailistingcontroller = AIListingController()
