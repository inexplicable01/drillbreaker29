from app.DBFunc.WashingtonZonesController import WashingtonZones
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric , ForeignKey
from typing import List, Optional

from app.DBFunc.CustomerController import Customer

Base = declarative_base()
from app.extensions import db


class CustomerZone(db.Model):
    __tablename__ = 'CustomerZone'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('WashingtonZones.id'), nullable=False)
    # city_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id'), nullable=False)


class CustomerZoneController:
    def __init__(self):
        self.db = db
        self.WashingtonZones = WashingtonZones
        self.Customer = Customer
        self.CustomerZone = CustomerZone

    def get_customer_zone(self, customer_id):
        # Fetch customer details
        customer = self.Customer.query.filter_by(id=customer_id).first()
        if not customer:
            return None, []  # Return None if the customer is not found
        return customer

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """
        Fetch customer details and ensure it returns an instance of Customer or None.
        """
        customer: Optional[Customer] = Customer.query.filter_by(id=customer_id).first()
        return customer

    def get_customer_zone_ids(self, customer_id: int) -> List[int]:
        """
        Return a list of zone_id values for the given customer_id.
        """
        rows = (
            self.CustomerZone.query
            .with_entities(self.CustomerZone.zone_id)
            .filter_by(customer_id=customer_id)
            .all()
        )
        # rows is a list of single-element tuples like [(511,), (204,), ...]
        return [zone_id for (zone_id,) in rows]

    def set_customer_zone_ids(self, customer_id: int, zone_ids: List[int]) -> List[int]:
        """
        Replace all zone assignments for a customer with the given zone_ids.
        Commits the change and returns the normalized list of ints.
        """
        # Normalize to ints (in case they come in as strings)
        cleaned_ids: List[int] = []
        for z in zone_ids:
            try:
                cleaned_ids.append(int(z))
            except (TypeError, ValueError):
                # skip bad values silently; you can raise if you prefer
                continue

        # Delete existing rows
        self.CustomerZone.query.filter_by(customer_id=customer_id).delete()

        # Insert new ones
        for zid in cleaned_ids:
            cz = self.CustomerZone(customer_id=customer_id, zone_id=zid)
            self.db.session.add(cz)

        self.db.session.commit()
        return cleaned_ids


customerzonecontroller = CustomerZoneController()
