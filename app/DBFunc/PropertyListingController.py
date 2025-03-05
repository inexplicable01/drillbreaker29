
from sqlalchemy import Column, BigInteger, Integer, String, LargeBinary, ForeignKey
from app.extensions import db
import zlib
import json



class PropertyListing(db.Model):
    __tablename__ = "PropertyListing"

    zpid = Column(BigInteger, ForeignKey("BriefListing.zpid", ondelete="CASCADE"), primary_key=True)
    compressed_data = Column(LargeBinary, nullable=False)  # Store compressed JSON data

    def set_data(self, data):
        """Compress and store JSON data."""
        if isinstance(data, dict):  # Ensure data is a dictionary before storing
            self.compressed_data = zlib.compress(json.dumps(data).encode("utf-8"))
        else:
            raise ValueError("Data must be a dictionary")

    def get_data(self):
        """Decompress and retrieve JSON data."""
        if self.compressed_data:
            return json.loads(zlib.decompress(self.compressed_data).decode("utf-8"))
        return None

    def __repr__(self):
        return f"<PropertyListing zpid={self.zpid}, price={self.price}, status={self.status}>"


class PropertyListingController:
    def __init__(self):
        self.db = db
        self.PropertyListing = PropertyListing

    def create_property(self, zpid, data):
        """Create a new property listing and store compressed JSON data."""
        new_property = self.PropertyListing(
            zpid=zpid,
            compressed_data=zlib.compress(json.dumps(data).encode("utf-8"))
        )
        self.db.session.add(new_property)
        self.db.session.commit()
        return new_property

    def get_property(self, zpid):
        """Retrieve property details by zpid."""
        listing = self.PropertyListing.query.get(zpid)
        if listing:
            return {
                "zpid": listing.zpid,
                "data": json.loads(zlib.decompress(listing.compressed_data).decode("utf-8"))
            }
        return None

    def update_property(self, zpid, data=None):
        """Update property details."""
        listing = self.PropertyListing.query.get(zpid)
        if listing:
            if data is not None:
                listing.compressed_data = zlib.compress(json.dumps(data).encode("utf-8"))
            self.db.session.commit()
            return listing
        return None

    def delete_property(self, zpid):
        """Delete a property listing."""
        listing = self.PropertyListing.query.get(zpid)
        if listing:
            self.db.session.delete(listing)
            self.db.session.commit()
            return True
        return False

    def get_all_properties(self, limit=100):
        """Retrieve all property listings with an optional limit."""
        listings = self.PropertyListing.query.limit(limit).all()
        return [
            {
                "zpid": listing.zpid,
                "data": json.loads(zlib.decompress(listing.compressed_data).decode("utf-8"))
            }
            for listing in listings
        ]
propertylistingcontroller = PropertyListingController()