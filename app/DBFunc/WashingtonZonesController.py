

from sqlalchemy.sql import func
from app.extensions import db
from datetime import datetime, timedelta
from app.config import Config
import pytz
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Double,Float, String, Text, BigInteger, DateTime, Numeric
from sqlalchemy.exc import SQLAlchemyError
# Base = declarative_base()
from geoalchemy2 import Geometry
from app.extensions import db
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

class WashingtonZones(db.Model):
    __tablename__ = 'WashingtonZones'

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id', ondelete="CASCADE"), nullable=False)  # Foreign Key

    neighbourhood = db.Column(db.String(255), nullable=False)
    neighbourhood_sub = db.Column(db.String(255), nullable=True)
    City = db.Column(db.String(255), nullable=False)
    # geometry = db.Column(Geometry('POLYGON'), nullable=True)
    # brief_listings = db.relationship('BriefListing', back_populates='zone', lazy=True)
    interests = db.relationship('CustomerNeighbourhoodInterest', back_populates='neighbourhood')

    def __repr__(self):
        return (f"<WashingtonZones(id={self.id},neighbourhood={self.neighbourhood}, neighbourhood_sub={self.neighbourhood_sub}, City={self.City})>")

from app.MapTools.MappingTools import WA_geojson_features
class WashingtonZonesController:
    def __init__(self):
        self.db = db
        self.WashingtonZones = WashingtonZones

    def getlist(self):

        WashingtonZones = self.WashingtonZones.query.all()
        return WashingtonZones

    def getneighbourhood(self,neighbourhood):
        return self.WashingtonZones.query.filter_by(neighbourhood_sub=neighbourhood).first()

    def get_zone_id_by_name(self,cityname,neighbourhood ):
        if neighbourhood is not None:
            zone = (self.WashingtonZones.query
                    .filter_by(neighbourhood_sub=neighbourhood)
                    .first())
            if zone:
                return zone
        # If no neighbourhood match, try to retrieve by city name
        return (self.WashingtonZones.query
                .filter_by(City=cityname)
                .first())

    def update_geometry_from_geojson(self, geojson_features):
        """
        Updates the WashingtonZones table by adding (or updating) geometry from GeoJSON.

        :param geojson_features: List of GeoJSON features containing neighborhood data and geometry.
        """
        for feature in geojson_features:
            try:
                # Extract properties and geometry
                properties = feature.get("properties", {})
                geom = feature.get("geometry")

                # Parse polygon/geometry using Shapely
                shapely_geom = shape(geom)  # Convert GeoJSON geometry into a Shapely geometry

                # Convert the Shapely geometry into WKT for database insertion
                geoalchemy_geom = from_shape(shapely_geom, srid=4326)  # WGS84 SRID

                # Get neighborhood name and sub-neighborhood
                neighborhood_name = properties.get("Name") or properties.get("neighborhood") or "Unknown Neighborhood"
                sub_neighborhood_name = properties.get("SubName") or properties.get("sub_neighborhood", None)

                # Check if the neighborhood already exists
                existing_zone = self.WashingtonZones.query.filter_by(
                    neighbourhood=neighborhood_name,
                    neighbourhood_sub=sub_neighborhood_name,
                ).first()

                if existing_zone:
                    # Update the existing record's geometry
                    existing_zone.geometry = geoalchemy_geom
                    print(f"Updated geometry for neighborhood: {neighborhood_name}")
                else:
                    # Create a new record with geometry
                    new_zone = WashingtonZones(
                        neighbourhood=neighborhood_name,
                        neighbourhood_sub=sub_neighborhood_name,
                        geometry=geoalchemy_geom,
                    )
                    db.session.add(new_zone)
                    print(f"Added new neighborhood with geometry: {neighborhood_name}")

            except SQLAlchemyError as e:
                print(f"Error updating geometry for feature: {feature}. Error: {str(e)}")

        # Commit all changes to the database
        try:
            db.session.commit()
            print("Geometry updated successfully in WashingtonZones.")
        except SQLAlchemyError as commit_error:
            db.session.rollback()
            print(f"Error committing changes to the database: {str(commit_error)}")




washingtonzonescontroller = WashingtonZonesController()
