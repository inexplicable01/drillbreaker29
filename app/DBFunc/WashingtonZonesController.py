

from sqlalchemy.sql import func

from app.DBFunc.WashingtonCitiesController import WashingtonCities
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
from geoalchemy2.shape import from_shape, to_shape

from shapely.geometry import shape, mapping
from shapely.wkt import loads
import json


class WashingtonZones(db.Model):
    __tablename__ = 'WashingtonZones'

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id', ondelete="CASCADE"), nullable=False)  # Foreign Key

    neighbourhood = db.Column(db.String(255), nullable=False)
    neighbourhood_sub = db.Column(db.String(255), nullable=True)
    City = db.Column(db.String(255), nullable=False)

    geometry = db.Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    # geometry = db.Column(Geometry('POLYGON'), nullable=True)
    def zonename(self):
        if self.neighbourhood_sub is not None:
            return f"{self.neighbourhood_sub}"
        elif self.neighbourhood is not None:
            return f"{self.neighbourhood}"
        else:
            return f"{self.City}"

    def get_polygon_string(self):
        """ Returns the geometry as a formatted polygon string """
        if not self.geometry:
            return None  # No geometry exists

        # Convert WKBElement to Shapely geometry
        shapely_geom = to_shape(self.geometry)

        # Extract coordinates
        if shapely_geom.geom_type == "Polygon":
            polygon_coords = shapely_geom.exterior.coords  # Get outer boundary
        elif shapely_geom.geom_type == "MultiPolygon":
            polygon_coords = shapely_geom.geoms[0].exterior.coords  # Get first polygon in MultiPolygon
        else:
            return None  # Not a valid polygon

        # Convert to formatted string: "lat lon, lat lon, lat lon"
        polygon_string = ", ".join(f"{lat} {lon}" for lon, lat in polygon_coords)

        return polygon_string

    def __repr__(self):
        return (f"<WashingtonZones(id={self.id},neighbourhood={self.neighbourhood}, neighbourhood_sub={self.neighbourhood_sub}, City={self.City})>")

from app.MapTools.MappingTools import WA_geojson_features
class WashingtonZonesController:
    def __init__(self):
        self.db = db
        self.WashingtonZones = WashingtonZones
        self.WashingtonCities = WashingtonCities

    def getlist(self):

        WashingtonZones = self.WashingtonZones.query.all()
        return WashingtonZones

    def getZonebyID(self,id):
        return self.WashingtonZones.query.filter_by(id=id).first()

    def getneighbourhood(self,neighbourhood):
        return self.WashingtonZones.query.filter_by(neighbourhood_sub=neighbourhood).first()

    def getzonebyName(self,zone):
        wzone = (self.WashingtonZones.query
                .filter_by(neighbourhood_sub=zone)
                .first())
        if wzone:
            return wzone
        wzone = (self.WashingtonZones.query
                 .filter_by(City=zone)
                 .first())
        if wzone:
            return wzone
        city_result = (self.WashingtonCities.query
                       .filter_by(City=zone)
                       .first())
        wzone = (self.WashingtonZones.query
                       .filter_by(city_id=city_result.city_id)
                       .first())
        if wzone:
            return wzone

    def get_zone_id_by_name(self,cityname,neighbourhood ):
        if neighbourhood is not None:
            zone = (self.WashingtonZones.query
                    .filter(self.WashingtonZones.neighbourhood_sub.ilike(f"%{neighbourhood.strip()}%"))  # Fuzzy match
                    .first())
            if zone:
                return zone
        # If no city match, search WashingtonZones for a match on neighbourhood
        zone_result = (self.WashingtonZones.query
                       .filter(self.WashingtonZones.neighbourhood.ilike(f"%{cityname.strip()}%"))
                       .first())
        if zone_result:
            return zone_result

        # If no neighbourhood match, try to retrieve by city name
        city_result = (self.WashingtonCities.query
                       .filter(self.WashingtonCities.City.ilike(f"%{cityname.strip()}%"))
                       .first())
        if city_result:
            zone_result = (self.WashingtonZones.query
                           .filter_by(city_id=city_result.city_id)
                           .first())
            if zone_result:
                return zone_result

        return None



        # If neither are found, return None
        return None

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
                # neighborhood_name = properties.get("Name") or properties.get("neighborhood") or "Unknown Neighborhood"
                # sub_neighborhood_name = properties.get("SubName") or properties.get("sub_neighborhood", None)
                if 'S_HOOD' in properties:
                    # Check if the neighborhood already exists
                    existing_zone = self.WashingtonZones.query.filter_by(
                        neighbourhood_sub=properties['S_HOOD']
                    ).first()
                else:
                    existing_zone = self.WashingtonZones.query.filter_by(
                        City=properties['CityName']
                    ).first()
                    if existing_zone is None:
                        existing_zone = self.WashingtonZones.query.filter_by(
                            neighbourhood=properties['CityName']
                        ).first()

                print(existing_zone)

                existing_zone.geometry = geoalchemy_geom
                db.session.merge(existing_zone)
                #     print(f"Updated geometry for neighborhood: {neighborhood_name}")
                # else:
                #     # Create a new record with geometry
                #     new_zone = WashingtonZones(
                #         neighbourhood=neighborhood_name,
                #         neighbourhood_sub=sub_neighborhood_name,
                #         geometry=geoalchemy_geom,
                #     )
                #     db.session.add(new_zone)
                #     print(f"Added new neighborhood with geometry: {neighborhood_name}")

            except SQLAlchemyError as e:
                print(f"Error updating geometry for feature: {feature}. Error: {str(e)}")

        # Commit all changes to the database
        try:
            db.session.commit()
            print("Geometry updated successfully in WashingtonZones.")
        except SQLAlchemyError as commit_error:
            db.session.rollback()
            print(f"Error committing changes to the database: {str(commit_error)}")

    def repair_from_geojson(self, citygeojson_features, WA_geojson_features, washingtoncitiescontroller):
        WashingtonZones = self.WashingtonZones.query.all()
        citycount={}
        for key,value in citygeojson_features.items():
            citycount[key]=0
        citycount['General']=0
        for zone in WashingtonZones:
            # print(zone)
            try:
                if zone.id<241:
                    continue
                    # print(zone.city.City)
                    # if zone.city.City in citygeojson_features:
                    #     S_HOOD = citygeojson_features[zone.city.City][citycount[zone.city.City]]['properties']['S_HOOD']
                    #     print(S_HOOD)
                    #     citycount[zone.city.City] +=1
                    #     zone.neighbourhood_sub = S_HOOD
                    #     db.session.merge(zone)
                    #     db.session.commit()

                else:
                    cityname = WA_geojson_features[citycount['General']]['properties']['CityName']
                    print(cityname)
                    WaCity = washingtoncitiescontroller.getCity(cityname)
                    if WaCity:
                        zone.city_id = WaCity.city_id
                        zone.City =WaCity.City
                        zone.neighbourhood = None
                        db.session.merge(zone)
                        db.session.commit()
                    else:
                        zone.neighbourhood = cityname
                        zone.city_id = None
                        zone.City = None
                        db.session.merge(zone)
                        db.session.commit()
                        # print("General")
                    citycount['General'] +=1
            except SQLAlchemyError as e:
                print("Rolling back due to: ", str(e))
                db.session.rollback()  # Explicitly rollback if an error occurs


    def getGeometryofZone(self,zoneid):
        zone = self.WashingtonZones.query.filter_by(id=zoneid).first()
        if zone:
            shape_geom = loads(zone.geometry)  # Convert WKT to Shapely geometry
            print(shape_geom)

    def getallGeoJson(self):
        geojson_features = []
        zones = self.WashingtonZones.query.all()
        for zone in zones:
            if zone.geometry:  # Ensure geometry is not NULL
                geojson_geom = json.loads(json.dumps(mapping(to_shape(zone.geometry))))
                if zone.neighbourhood_sub:
                    geojson_features.append({
                        "type": "Feature",
                        "properties": {
                            "S_HOOD": zone.neighbourhood_sub,
                        },
                        "geometry": geojson_geom  # Convert string to JSON
                    })
                else:
                    geojson_features.append({
                        "type": "Feature",
                        "properties": {
                            "CityName": zone.City if zone.City else zone.neighbourhood
                        },
                        "geometry": geojson_geom # Convert string to JSON
                    })
        return geojson_features


washingtonzonescontroller = WashingtonZonesController()
