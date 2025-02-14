from app.DBModels.Customer import Customer
from app.DBModels.BriefListing import BriefListing
from app.DBModels.CustomerZpid import CustomerZpid
from app import db

# Define relationships explicitly
Customer.customerzpid_array = db.relationship(
    'CustomerZpid',  # Use the association table explicitly
    back_populates="customer",
    cascade="all, delete-orphan"
)

BriefListing.customers = db.relationship(
    'CustomerZpid',
    back_populates="brief_listing",
    cascade="all, delete-orphan"
)

CustomerZpid.customer = db.relationship(
    "Customer",
    back_populates="customerzpid_array"
)

CustomerZpid.brief_listing = db.relationship(
    "BriefListing",
    back_populates="customers"
)
