from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime , Numeric
from datetime import datetime
Base = declarative_base()
from app.extensions import db

CACHE_EXPIRATION_DAYS = 7  # Only recalculate if older than 7 days

class CachedInvestmentData(db.Model):
    __tablename__ = 'cached_investment_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Unique ID for each entry
    zpid = db.Column(db.String, db.ForeignKey('BriefListing.zpid'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    mls = db.Column(db.String)
    address = db.Column(db.String)
    price = db.Column(db.Float)
    estimated_rent = db.Column(db.Float)
    mortgage = db.Column(db.Float)
    property_tax = db.Column(db.Float)
    hoa_fee = db.Column(db.Float)
    insurance = db.Column(db.Float)
    maintenance = db.Column(db.Float)
    cash_flow = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CachedInvestmentDataController():

    def __init__(self):
        self.db = db
        self.CachedInvestmentData = CachedInvestmentData
        self.CACHE_EXPIRATION_DAYS=CACHE_EXPIRATION_DAYS

    def getAllCleaners(self):
        return CachedInvestmentData.query.all()

    def get_cached_listing(self, zpid, customer_id):
        """Retrieve cached investment data as a dictionary if it's fresh."""
        cached_listing = self.CachedInvestmentData.query.filter_by(zpid=zpid, customer_id=customer_id).first()

        if cached_listing:
            # Check if cache is expired
            if cached_listing.last_updated < datetime.utcnow() - timedelta(days=self.CACHE_EXPIRATION_DAYS):
                return None  # Expired data, force recalculation

            # Convert SQLAlchemy object to dictionary
            return {
                'id': cached_listing.id,
                'zpid': cached_listing.zpid,
                'mls': cached_listing.mls,
                'address': cached_listing.address,
                'price': f"${cached_listing.price:,.2f}",
                'estimated_rent': f"${cached_listing.estimated_rent:,.2f}",
                'mortgage': f"${cached_listing.mortgage:,.2f}",
                'property_tax': f"${cached_listing.property_tax:,.2f}",
                'hoa_fee': f"${cached_listing.hoa_fee:,.2f}",
                'insurance': f"${cached_listing.insurance:,.2f}",
                'maintenance': f"${cached_listing.maintenance:,.2f}",
                'cash_flow': f"${cached_listing.cash_flow:,.2f}",
                'last_updated': cached_listing.last_updated.strftime('%Y-%m-%d %H:%M:%S')  # Convert to string format
            }

        return None  # No cached data found

    def adddata(self, zpid, customer_id, mls, address, price, estimated_rent, mortgage, property_tax, hoa_fee, insurance, maintenance, cash_flow):
        """Adds a new cached investment entry or updates an existing one."""
        try:
            # Check if the record exists for the same customer and listing
            existing_entry = self.CachedInvestmentData.query.filter_by(zpid=zpid, customer_id=customer_id).first()

            if existing_entry:
                # Update existing record
                existing_entry.mls = mls
                existing_entry.address = address
                existing_entry.price = price
                existing_entry.estimated_rent = estimated_rent
                existing_entry.mortgage = mortgage
                existing_entry.property_tax = property_tax
                existing_entry.hoa_fee = hoa_fee
                existing_entry.insurance = insurance
                existing_entry.maintenance = maintenance
                existing_entry.cash_flow = cash_flow
                existing_entry.last_updated = datetime.utcnow()
            else:
                # Insert new record
                new_entry = self.CachedInvestmentData(
                    zpid=zpid,
                    customer_id=customer_id,
                    mls=mls,
                    address=address,
                    price=price,
                    estimated_rent=estimated_rent,
                    mortgage=mortgage,
                    property_tax=property_tax,
                    hoa_fee=hoa_fee,
                    insurance=insurance,
                    maintenance=maintenance,
                    cash_flow=cash_flow
                )
                self.db.session.add(new_entry)

            # Commit transaction
            self.db.session.commit()

        except Exception as e:
            self.db.session.rollback()  # Rollback transaction in case of error
            print(f"Error in adddata: {str(e)}")

cachedinvestmentdatacontroller = CachedInvestmentDataController()