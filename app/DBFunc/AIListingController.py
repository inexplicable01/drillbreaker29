from app.DBModels.AIListingComments import AIListingComments
from sqlalchemy.sql import func

from app.extensions import db
# from app.DB
from datetime import datetime, timedelta
from app.DBFunc.SeattlleNeighbourhoodsController import seattleneighbourhoodcontroller
from app.config import Config, SW
import pytz

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


ailistingcontroller = AIListingController()
