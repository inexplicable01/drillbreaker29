from app.DBModels.SeattleNeighbourhoods import SeattleNeighbourhoods
from sqlalchemy.sql import func
from app.extensions import db
from app.DBModels.Customer import Customer
from app.DBModels.CustomerNeighbourhoodInterest import CustomerNeighbourhoodInterest
from datetime import datetime, timedelta
from app.config import Config
import pytz

class CustomerNeighbourhoodInterestController:
    def __init__(self):
        self.db = db
        self.SeattleNeighbourhoods = SeattleNeighbourhoods
        self.Customer = Customer
        self.CustomerNeighbourhoodInterest = CustomerNeighbourhoodInterest

    def get_customer_neighbourhood_interest(self, customer_id):
        # Fetch customer details
        customer = self.Customer.query.filter_by(id=customer_id).first()
        if not customer:
            return None, []  # Return None if the customer is not found

        # Fetch neighborhoods of interest for the customer
        interests = (
            self.db.session.query(self.CustomerNeighbourhoodInterest)
            .filter(self.CustomerNeighbourhoodInterest.customer_id == customer_id)
            .all()
        )

        # Format customer details
        customer_data = {
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone
        }

        # Format neighbourhood interests
        neighbourhoods = []
        for n in interests:

            neighbourhoods.append({
                "neighbourhood": n.neighbourhood.neighbourhood,
                "neighbourhood_sub": n.neighbourhood.neighbourhood_sub,
                "city": n.WashingtonCities.city
            })


        return customer_data, neighbourhoods

customerneighbourhoodinterestcontroller = CustomerNeighbourhoodInterestController()
