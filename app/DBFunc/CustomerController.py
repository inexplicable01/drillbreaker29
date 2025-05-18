from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()
from app.extensions import db


class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    minprice = db.Column(db.Integer, nullable=True)
    idealprice = db.Column(db.Integer, nullable=True)
    maxprice = db.Column(db.Integer, nullable=True)
    idealsqft = db.Column(db.Integer, nullable=True)
    minsqft = db.Column(db.Integer, nullable=True)
    maxsqft = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, nullable=True)
    last_contacted =  db.Column(db.DateTime, default=datetime.utcnow)
    lot_size = db.Column(db.Integer, nullable=True)
    parkingspaceneeded = db.Column(db.Integer, nullable=True)
    customer_type_id = db.Column(db.Integer, db.ForeignKey('CustomerType.id'))
    maincity_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id'))

    # interests = db.relationship('CustomerZone', back_populates='customer')


    def __str__(self):
        return (
            f"Customer(ID: {self.id}, Name: {self.name} {self.lastname}, Email: {self.email}, "
            f"Phone: {self.phone}, Price Range: {self.minprice}-{self.maxprice} (Ideal: {self.idealprice}), "
            f"Square Footage: {self.minsqft}-{self.maxsqft} (Ideal: {self.idealsqft}))"
        )

class CustomerController():

    def __init__(self):
        self.db = db
        self.Customer = Customer

    def getAllCustomer(self):
        return Customer.query.all()

    def getCustomerByID(self, id):
        return Customer.query.get(id)

    def getCustomerByEmail(self, email):
        return Customer.query.filter_by(email=email).first()

    def getCustomerZpidInterests(self):
        customers = Customer.query.options(db.joinedload(Customer.customerzpid_array)).all()
        return customers

    def get_active_customers(self, as_dict=False):
        """Retrieve a list of active customers.

        Args:
            as_dict (bool): If True, returns data as a list of dictionaries.

        Returns:
            List of Customer objects or dictionaries.
        """
        customers = self.Customer.query.filter_by(active=True).all()

        if as_dict:
            return [
                {
                    "id": customer.id,
                    "name": customer.name,
                    "lastname": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "price_range": f"{customer.minprice}-{customer.maxprice} (Ideal: {customer.idealprice})",
                    "square_footage": f"{customer.minsqft}-{customer.maxsqft} (Ideal: {customer.idealsqft})",
                    "last_contacted": customer.last_contacted.strftime(
                        "%Y-%m-%d %H:%M:%S") if customer.last_contacted else None
                }
                for customer in customers
            ]

        return customers  # Return as list of Customer objects by default


customercontroller = CustomerController()