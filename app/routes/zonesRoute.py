# app/views/zones.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.extensions import db  # needed for commit/rollback when updating geom

zones_bp = Blueprint("zones", __name__, url_prefix="/zones")

@zones_bp.route("/new", methods=["GET"])
def new_zone():
    return render_template("zones_new.html")

@zones_bp.route("/geojson", methods=["GET"])
def zones_geojson():
    # Your controller’s getallGeoJson() returns a list of Features (per your code).
    features = washingtonzonescontroller.getallGeoJson()
    return jsonify({"type": "FeatureCollection", "features": features})

@zones_bp.route("", methods=["POST"])
def create_zone():
    city_name = request.form.get("city_name") or None
    neighbourhood = request.form.get("neighbourhood") or None
    neighbourhood_sub = request.form.get("neighbourhood_sub") or None
    latlon_string = request.form.get("latlon_string") or None
    geojson_text = request.form.get("geojson_text") or None

    geojson_geom = None
    if geojson_text:
        try:
            import json
            geo = json.loads(geojson_text)
            geojson_geom = geo.get("geometry") if geo.get("type") == "Feature" else geo
        except Exception:
            msg = "Invalid GeoJSON."
            if request.headers.get("X-Requested-With") == "fetch":
                return jsonify({"ok": False, "message": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("zones.new_zone"))

    if not (latlon_string or geojson_geom):
        msg = "Provide either a drawn polygon (GeoJSON) or a 'lat lon' string."
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": False, "message": msg}), 400
        flash(msg, "warning")
        return redirect(url_for("zones.new_zone"))

    try:
        zone = washingtonzonescontroller.add_zone(
            city_name=city_name,
            neighbourhood=neighbourhood,
            neighbourhood_sub=neighbourhood_sub,
            geojson_geom=geojson_geom,
            latlon_string=latlon_string,
            upsert_if_exists=False
        )
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": True, "id": zone.id})
        flash(f"Zone created (id={zone.id}).", "success")
        return redirect(url_for("zones.new_zone"))
    except SQLAlchemyError:
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": False, "message": "DB error creating zone."}), 500
        flash("Database error creating zone.", "danger")
        return redirect(url_for("zones.new_zone"))
    except Exception as e:
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": False, "message": str(e)}), 400
        flash(str(e), "danger")
        return redirect(url_for("zones.new_zone"))

# -----------------------------
# Additions: edit existing zone
# -----------------------------

@zones_bp.route("/edit/<int:zone_id>", methods=["GET"])
def edit_zone(zone_id):
    """Render a simple Leaflet editor page for a given zone."""
    return render_template("edit_zone.html", zone_id=zone_id)

@zones_bp.route("/geojson/<int:zone_id>", methods=["GET"])
def get_zone_geojson(zone_id):
    """Return a single zone as a GeoJSON Feature (for editing)."""
    zone = washingtonzonescontroller.getZonebyID(zone_id)
    if not zone or not zone.geometry:
        return jsonify({"error": "Zone not found"}), 404

    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping

    geom = to_shape(zone.geometry)
    feature = {
        "type": "Feature",
        "properties": {
            "id": zone.id,
            "City": zone.City,
            "S_HOOD": zone.neighbourhood_sub,
            "Neighbourhood": zone.neighbourhood,
        },
        "geometry": mapping(geom)
    }
    return jsonify(feature)

@zones_bp.route("/update_geom/<int:zone_id>", methods=["POST"])
def update_zone_geojson(zone_id):
    """Accept a GeoJSON Feature or bare geometry and update the zone geometry."""
    try:
        payload = request.get_json(force=True, silent=False)

        if not payload:
            return jsonify({"ok": False, "error": "No JSON body"}), 400

        # Accept Feature or bare geometry
        geom_obj = payload.get("geometry") if payload.get("type") == "Feature" else payload
        if not geom_obj:
            return jsonify({"ok": False, "error": "Missing geometry"}), 400

        from shapely.geometry import shape as shp_from_geojson
        from geoalchemy2.shape import from_shape

        shp = shp_from_geojson(geom_obj['geojson_geom'])

        zone = washingtonzonescontroller.getZonebyID(zone_id)
        if not zone:
            return jsonify({"ok": False, "error": "Zone not found"}), 404

        zone.geometry = from_shape(shp, srid=4326)
        db.session.commit()
        return jsonify({"ok": True})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": "Database error"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
