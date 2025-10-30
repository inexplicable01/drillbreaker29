

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
# --- add these imports near your other imports ---
from typing import Optional, List, Tuple, Dict
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.geometry import shape as shp_from_geojson
from shapely.validation import make_valid
from geoalchemy2.shape import from_shape
from sqlalchemy.exc import SQLAlchemyError

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

# from app.MapTools.MappingTools import WA_geojson_features
class WashingtonZonesController:
    def __init__(self):
        self.db = db
        self.WashingtonZones = WashingtonZones
        self.WashingtonCities = WashingtonCities

    def getlist(self):

        WashingtonZones = self.WashingtonZones.query.all()
        return WashingtonZones

    def getZoneListbyCity_id(self, city_id):
        return self.WashingtonZones.query.filter_by(city_id=city_id).all()

    def getZonebyID(self,id):
        return self.WashingtonZones.query.filter_by(id=id).first()

    def getneighbourhood(self,neighbourhood):
        return self.WashingtonZones.query.filter_by(neighbourhood_sub=neighbourhood).first()

    def load_zone_polygons(self, city_name=None, include_bbox=True, fix_invalid=True):
        """
        Return a list of zone polygon records for reuse in point-in-polygon checks.

        Each item is a dict:
          {
            "id": <zone id>,
            "city": <City or None>,
            "neighbourhood": <neighbourhood or None>,
            "neighbourhood_sub": <neighbourhood_sub or None>,
            "geom": <Shapely geometry (Polygon or MultiPolygon)>,
            "bbox": (minx, miny, maxx, maxy)   # only if include_bbox=True
          }

        Notes:
          - Shapely uses (lon, lat) order internally.
          - Use this once to build a cache, then loop listings against these geoms.
        """
        from geoalchemy2.shape import to_shape
        from shapely.validation import make_valid

        q = (self.WashingtonZones.query
             .filter(self.WashingtonZones.geometry.isnot(None)))

        if city_name:
            q = q.filter(self.WashingtonZones.City.ilike(city_name.strip()))

        out = []
        for z in q.yield_per(200):
            try:
                g = to_shape(z.geometry)  # GeoAlchemy -> Shapely
            except Exception:
                continue

            if fix_invalid and not g.is_valid:
                try:
                    g = make_valid(g)
                except Exception:
                    # Skip irreparable geometries
                    continue

            rec = {
                "zone": z,
                "id": z.id,
                "city": z.City,
                "neighbourhood": z.neighbourhood,
                "neighbourhood_sub": z.neighbourhood_sub,
                "geom": g
            }
            if include_bbox:
                rec["bbox"] = g.bounds  # (minx, miny, maxx, maxy) == (lon_min, lat_min, lon_max, lat_max)

            out.append(rec)

        return out


    def getzonebyName(self,zonename):
        wzone = (self.WashingtonZones.query
                .filter_by(neighbourhood_sub=zonename)
                .first())
        if wzone:
            return wzone
        wzone = (self.WashingtonZones.query
                 .filter_by(City=zonename)
                 .first())
        if wzone:
            return wzone
        city_result = (self.WashingtonCities.query
                       .filter_by(City=zonename)
                       .first())
        if city_result:
            wzone = (self.WashingtonZones.query
                           .filter_by(city_id=city_result.city_id)
                           .first())
            if wzone:
                return wzone
        return None

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

    # In WashingtonZonesController
    from shapely.geometry import mapping
    from geoalchemy2.shape import to_shape
    import json

    def getallGeoJson(self):
        """
        Return a list[Feature] with consistent properties so the UI can
        populate form fields on click.
        Properties included (when not None):
          - id
          - CityName
          - Neighbourhood
          - S_HOOD
        """
        features = []
        q = self.WashingtonZones.query.filter(self.WashingtonZones.geometry.isnot(None))

        for zone in q.all():
            geom_js = mapping(to_shape(zone.geometry))  # dict (not a string)

            props = {
                "id": zone.id,
                "CityName": zone.City if zone.City else None,
                "Neighbourhood": zone.neighbourhood if zone.neighbourhood else None,
                "S_HOOD": zone.neighbourhood_sub if zone.neighbourhood_sub else None,
            }
            # drop None to keep payload tidy
            props = {k: v for k, v in props.items() if v is not None}

            features.append({
                "type": "Feature",
                "properties": props,
                "geometry": geom_js
            })

        return features

    def _polygon_from_latlon_list(self, latlon_points: List[Tuple[float, float]]) -> Polygon:
        """
        latlon_points: [(lat, lon), (lat, lon), ...] — closed or open ring
        NOTE: Shapely expects (lon, lat), so we flip on ingest.
        """
        if not latlon_points or len(latlon_points) < 3:
            raise ValueError("Need at least 3 points for a polygon.")
        ring_lonlat = [(lon, lat) for (lat, lon) in latlon_points]
        if ring_lonlat[0] != ring_lonlat[-1]:
            ring_lonlat.append(ring_lonlat[0])
        return Polygon(ring_lonlat)

    def _polygon_from_latlon_string(self, latlon_string: str) -> Polygon:
        """
        latlon_string: 'lat lon, lat lon, lat lon, ...'
        Parses and builds a Polygon (auto-closes the ring if needed).
        """
        pts: List[Tuple[float, float]] = []
        for pair in latlon_string.split(","):
            pair = pair.strip()
            if not pair:
                continue
            lat_str, lon_str = pair.split()
            pts.append((float(lat_str), float(lon_str)))
        return self._polygon_from_latlon_list(pts)

        # ---------- Add / upsert zone ----------

    def add_zone(
            self,
            city_name: Optional[str] = None,
            neighbourhood: Optional[str] = None,
            neighbourhood_sub: Optional[str] = None,
            geojson_geom: Optional[Dict] = None,
            latlon_points: Optional[List[Tuple[float, float]]] = None,
            latlon_string: Optional[str] = None,
            srid: int = 4326,
            upsert_if_exists: bool = True
    ):
        """
        Create (or upsert) a WashingtonZones row with geometry.
        Provide one of: geojson_geom, latlon_points, latlon_string.
        Keeps your 'lat lon' convention for inputs (we flip to lon/lat for Shapely).
        """
        # 1) Resolve city_id and City field
        city_id: Optional[int] = None
        City: Optional[str] = None
        if city_name:
            city_name_q = city_name.strip()
            city_row = (self.WashingtonCities.query
                        .filter(self.WashingtonCities.City.ilike(city_name_q))
                        .first())
            if city_row:
                city_id = city_row.city_id
                City = city_row.City
            else:
                City = city_name_q  # allow storing City text even if not in WashingtonCities

        # 2) Build a Shapely geometry from provided input
        if geojson_geom is not None:
            shp = shp_from_geojson(geojson_geom)
        elif latlon_points is not None:
            shp = self._polygon_from_latlon_list(latlon_points)
        elif latlon_string is not None:
            shp = self._polygon_from_latlon_string(latlon_string)
        else:
            raise ValueError("Provide one of: geojson_geom, latlon_points, latlon_string.")

        # 3) Make valid & coerce to MultiPolygon (PostGIS column is MULTIPOLYGON)
        shp = make_valid(shp)
        if isinstance(shp, Polygon):
            shp = MultiPolygon([shp])

        # 4) Convert to GeoAlchemy geometry
        g = from_shape(shp, srid=srid)

        # 5) Upsert / insert
        zone = None
        if upsert_if_exists:
            if neighbourhood_sub:
                zone = (self.WashingtonZones.query
                        .filter(self.WashingtonZones.neighbourhood_sub.ilike(neighbourhood_sub.strip()))
                        .first())
            if zone is None and neighbourhood:
                zone = (self.WashingtonZones.query
                        .filter(self.WashingtonZones.neighbourhood.ilike(neighbourhood.strip()))
                        .first())
            if zone is None and City:
                zone = (self.WashingtonZones.query
                        .filter(self.WashingtonZones.City.ilike(City))
                        .first())

        if zone is None:
            zone = self.WashingtonZones()

        zone.city_id = city_id
        zone.City = City
        zone.neighbourhood = neighbourhood
        zone.neighbourhood_sub = neighbourhood_sub
        zone.geometry = g

        try:
            db.session.add(zone)
            db.session.commit()
            return zone  # return the ORM object (now with id)
        except SQLAlchemyError:
            db.session.rollback()
            raise


washingtonzonescontroller = WashingtonZonesController()
