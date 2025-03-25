
from sqlalchemy.sql import func
from app.extensions import db


from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func, String
from app.extensions import db

class CustomerType(db.Model):
    __tablename__ = 'CustomerType'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<CustomerType(id={self.id}, type_name='{self.type_name}')>"


class CustomerTypeController:
    def __init__(self):
        self.db = db
        self.CustomerType = CustomerType

    def add_customer_type(self, type_name):
        """
        Adds a new customer type if it doesn't already exist.
        """
        existing = self.CustomerType.query.filter_by(type_name=type_name).first()
        if existing:
            return existing

        new_type = self.CustomerType(type_name=type_name)
        self.db.session.add(new_type)
        self.db.session.commit()
        return new_type

    def get_customer_type_by_id(self, type_id):
        """
        Retrieves a customer type by ID.
        """
        return self.CustomerType.query.get(type_id)

    def get_all_customer_types(self):
        """
        Retrieves all customer types.
        """
        return self.CustomerType.query.order_by(self.CustomerType.id.asc()).all()

    def customer_type_exists(self, type_name):
        """
        Checks whether a customer type exists by name.
        """
        return self.CustomerType.query.filter_by(type_name=type_name).first() is not None

customertypecontroller = CustomerTypeController()