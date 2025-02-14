from app.DBModels.SeattleNeighbourhoods import SeattleNeighbourhoods
from app.extensions import db
from app.DBModels.Customer import Customer
from app.DBModels.CustomerNeighbourhoodInterest import CustomerNeighbourhoodInterest
from typing import Optional

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
        locations = []
        for n in interests:
            if n.neighbourhood:
                locations.append({
                    "neighbourhood": n.neighbourhood.neighbourhood,
                    "neighbourhood_sub": n.neighbourhood.neighbourhood_sub,
                    "city": n.WashingtonCities.city
                })
            else:
                locations.append({
                    "neighbourhood": None,
                    "neighbourhood_sub": None,
                    "city": n.WashingtonCities.city
                })


        return customer_data, locations

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """
        Fetch customer details and ensure it returns an instance of Customer or None.
        """
        customer: Optional[Customer] = Customer.query.filter_by(id=customer_id).first()
        return customer

customerneighbourhoodinterestcontroller = CustomerNeighbourhoodInterestController()
