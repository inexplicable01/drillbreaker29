from app.DBModels.CustomerZpid import CustomerZpid
from sqlalchemy.sql import func, or_, distinct
from app.extensions import db
from app.useful_func import safe_float_conversion,safe_int_conversion,print_and_log
from datetime import  datetime, timedelta
from app.UsefulAPI.UseFulAPICalls import get_neighborhood
from app.config import Config
import decimal
from sqlalchemy import distinct
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief


class CustomerZpidController():

    def __init__(self):
        self.db = db
        self.CustomerZpid = CustomerZpid

    def getAllCustomerzpids(self):
        try:
            return self.CustomerZpid.query.all()
        except Exception as e:
            print_and_log(f"Error retrieving all CustomerZpids: {str(e)}")
            return []

    def getAllZPIDS_Customerzpids(self):
        try:
            zpids=[]
            for customerzpid  in self.CustomerZpid.query.all():
                zpids.append(customerzpid.zpid)
            return zpids
        except Exception as e:
            print_and_log(f"Error retrieving all CustomerZpids: {str(e)}")
            return []

    # Retrieve a single CustomerZpid by ID
    def getCustomerZpidByID(self, id):
        try:
            return self.CustomerZpid.query.filter_by(id=id).first()
        except Exception as e:
            print_and_log(f"Error retrieving CustomerZpid by ID: {str(e)}")
            return None

    def getCustomerZpidByCustomerAndZpid(self,customer_id, zpid):
        return CustomerZpid.query.filter_by(customer_id=customer_id, zpid=zpid).first()


    def getlistingsofCustomerByCustomerID(self, customerid):
        try:
            customerzpids = self.CustomerZpid.query.filter_by(customer_id=customerid).all()
            return customerzpids
        except Exception as e:
            print_and_log(f"Error retrieving CustomerZpid by ID: {str(e)}")
            return None

    def getCustomerZpidByZpid(self, zpid):
        try:
            return self.CustomerZpid.query.filter_by(zpid=zpid).all()
        except Exception as e:
            print_and_log(f"Error retrieving CustomerZpid by ID: {str(e)}")
            return None

    def retire_customer_zpid(self,customerzpid_id):
        customer_zpid = CustomerZpid.query.filter_by(id=customerzpid_id).first()
        if customer_zpid:
            customer_zpid.is_retired = True
            self.db.session.merge(customer_zpid)
            self.db.session.commit()
            return True
        return False

    def delete_customerzpid(self, zpid, customer_id):
        """Permanently delete a CustomerZpid entry."""
        customer_zpid = CustomerZpid.query.filter_by(zpid=zpid, customer_id=customer_id).first()

        if customer_zpid:
            self.db.session.delete(customer_zpid)  # Delete from the database
            self.db.session.commit()
            return True  # Successfully deleted

        return False  # No matching record found

    # Save a new CustomerZpid or update an existing one
    def saveCustomerzpid(self, brieflisting, customer):
        """
        Save or update a CustomerZpid entry based on the provided BriefListing and Customer.

        :param brieflisting: BriefListing object (must include zpid).
        :param customer: Customer object.
        """
        try:
            # Check if a CustomerZpid already exists for this customer and zpid
            existing_customerzpid = self.CustomerZpid.query.filter_by(
                zpid=brieflisting.zpid, customer_id=customer.id
            ).first()

            if existing_customerzpid:
                # Update existing record if different data is provided
                print_and_log(f"Already EXISTS CustomerZpid for customer_id {customer.id} with zpid {brieflisting.zpid}")
            else:
                # Create a new record
                new_customerzpid = self.CustomerZpid(
                    zpid=brieflisting.zpid,
                    customer_id=customer.id,
                    created_at=datetime.utcnow()
                )
                self.db.session.add(new_customerzpid)
                print_and_log(f"Created new CustomerZpid for customer_id {customer.id} with zpid {brieflisting.zpid}")

            # Commit the database transaction
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print_and_log(f"Error saving CustomerZpid: {str(e)}")
            return False

    def update_listing_snapshot(self, customerzpid, listing, changes_detected=None):
        """
        Update the snapshot for a customer's tracked listing.
        Handles the database commit.

        :param customerzpid: CustomerZpid object
        :param listing: BriefListing object with current state
        :param changes_detected: Optional list of change descriptions
        :return: True if successful, False otherwise
        """
        try:
            customerzpid.update_snapshot(listing, changes_detected)
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print_and_log(f"Error updating snapshot for customer {customerzpid.customer_id}, zpid {customerzpid.zpid}: {str(e)}")
            return False

    def mark_listing_alerted(self, customerzpid):
        """
        Mark that an alert was sent for this customer's tracked listing.
        Handles the database commit.

        :param customerzpid: CustomerZpid object
        :return: True if successful, False otherwise
        """
        try:
            customerzpid.mark_alerted()
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print_and_log(f"Error marking alerted for customer {customerzpid.customer_id}, zpid {customerzpid.zpid}: {str(e)}")
            return False


customerzpidcontroller = CustomerZpidController()