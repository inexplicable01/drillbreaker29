
from sqlalchemy.sql import func
from app.extensions import db


from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func
from app.extensions import db

class CustomerDescription(db.Model):
    __tablename__ = 'CustomerDescription'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('Customer.id', ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    def __repr__(self):
        return f"<CustomerDescriptions(id={self.id}, customer_id={self.customer_id}, description='{self.description[:50]}...', created_at={self.created_at})>"






class CustomerDescriptionController:
    def __init__(self):
        self.db = db
        self.CustomerDescription = CustomerDescription

    @staticmethod
    def check_existing_description(customer_id) -> [CustomerDescription]:
        """
        Checks if any descriptions exist for the given customer.
        Returns a list of descriptions if they exist.
        """
        existing_descriptions = CustomerDescription.query.filter_by(customer_id=customer_id).all()
        return existing_descriptions

    @staticmethod
    def add_customer_description(customer_id, description):
        """
        Adds a new description entry for a given customer.
        """
        new_description = CustomerDescription(
            customer_id=customer_id,
            description=description
        )
        db.session.add(new_description)
        db.session.commit()

    def retrieve_latest_description(self, customer_id):
        """
        Retrieves the latest description entry for a given customer.
        """
        latest_description = (
            self.db.session.query(self.CustomerDescription)
            .filter(self.CustomerDescription.customer_id == customer_id)
            .order_by(self.CustomerDescription.created_at.desc())
            .first()
        )
        return latest_description

    def retrieve_all_descriptions(self, customer_id):
        """
        Retrieves all descriptions for a given customer, ordered by most recent first.
        """
        all_descriptions = (
            self.db.session.query(self.CustomerDescription)
            .filter(self.CustomerDescription.customer_id == customer_id)
            .order_by(self.CustomerDescription.created_at.desc())
            .all()
        )
        return all_descriptions


customer_description_controller = CustomerDescriptionController()
