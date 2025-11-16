# app/views/zones.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.DBFunc.WashingtonZonesController import washingtonzonescontroller
from app.DBFunc.CustomerController import customercontroller
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.extensions import db  # needed for commit/rollback when updating geom
import json

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
    is_fetch = request.headers.get("X-Requested-With") == "fetch"

    # --- Branch 1: JSON payload from fetch (map UI) ---
    if request.is_json:
        data = request.get_json(silent=True) or {}

        city_name = data.get("city_name") or None
        neighbourhood = data.get("neighbourhood") or None
        neighbourhood_sub = data.get("neighbourhood_sub") or None
        latlon_string = data.get("latlon_string") or None  # probably None from map UI
        geojson_geom = data.get("geojson_geom") or None    # already a geometry dict

    # --- Branch 2: old form-based flow (e.g. /zones/new form post) ---
    else:
        city_name = request.form.get("city_name") or None
        neighbourhood = request.form.get("neighbourhood") or None
        neighbourhood_sub = request.form.get("neighbourhood_sub") or None
        latlon_string = request.form.get("latlon_string") or None
        geojson_text = request.form.get("geojson_text") or None

        geojson_geom = None
        if geojson_text:
            try:
                geo = json.loads(geojson_text)
                # Accept either Feature or raw geometry
                geojson_geom = geo.get("geometry") if geo.get("type") == "Feature" else geo
            except Exception:
                msg = "Invalid GeoJSON."
                if is_fetch:
                    return jsonify({"ok": False, "message": msg}), 400
                flash(msg, "danger")
                return redirect(url_for("zones.new_zone"))

    # --- Shared validation ---
    if not (latlon_string or geojson_geom):
        msg = "Provide either a drawn polygon (GeoJSON) or a 'lat lon' string."
        if is_fetch:
            return jsonify({"ok": False, "message": msg}), 400
        flash(msg, "warning")
        return redirect(url_for("zones.new_zone"))

    # --- Create zone ---
    try:
        zone = washingtonzonescontroller.add_zone(
            city_name=city_name,
            neighbourhood=neighbourhood,
            neighbourhood_sub=neighbourhood_sub,
            geojson_geom=geojson_geom,
            latlon_string=latlon_string,
            upsert_if_exists=False,
        )
        if is_fetch:
            return jsonify({"ok": True, "id": zone.id})
        flash(f"Zone created (id={zone.id}).", "success")
        return redirect(url_for("zones.new_zone"))

    except SQLAlchemyError:
        if is_fetch:
            return jsonify({"ok": False, "message": "DB error creating zone."}), 500
        flash("Database error creating zone.", "danger")
        return redirect(url_for("zones.new_zone"))

    except Exception as e:
        if is_fetch:
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
def update_zone_geom(zone_id):
    is_fetch = request.headers.get("X-Requested-With") == "fetch"
    data = request.get_json(silent=True) or {}

    city_name = data.get("city_name") or None
    neighbourhood = data.get("neighbourhood") or None
    neighbourhood_sub = data.get("neighbourhood_sub") or None
    geojson_geom = data.get("geojson_geom") or None

    if not geojson_geom:
        msg = "Missing geojson_geom for update."
        if is_fetch:
            return jsonify({"ok": False, "message": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("zones.new_zone"))

    try:
        washingtonzonescontroller.update_zone(
            zone_id=zone_id,
            city_name=city_name,
            neighbourhood=neighbourhood,
            neighbourhood_sub=neighbourhood_sub,
            geojson_geom=geojson_geom,
        )
        if is_fetch:
            return jsonify({"ok": True, "id": zone_id})
        flash(f"Zone {zone_id} updated.", "success")
        return redirect(url_for("zones.new_zone"))
    except SQLAlchemyError:
        if is_fetch:
            return jsonify({"ok": False, "message": "DB error updating zone."}), 500
        flash("Database error updating zone.", "danger")
        return redirect(url_for("zones.new_zone"))

@zones_bp.route('/customer_zones', methods=['GET'])
def customer_zones_map():
    # All customers for dropdown
    customers = customercontroller.getCustomerByIDType(5)

    # Default selected customer
    selected_customer_id = request.args.get('customer_id', type=int)
    if not selected_customer_id and customers:
        selected_customer_id = customers[0].id

    # Get this customer's assigned zones (list of zone_ids)

    if selected_customer_id:
        assigned_zone_ids = customerzonecontroller.get_customer_zone_ids(selected_customer_id)
    else:
        assigned_zone_ids = []

    # All zones as GeoJSON
    features = washingtonzonescontroller.getallGeoJson()

    return render_template(
        'ClickAbleMap/ZoneMapWIds.html',
        geojson_features=features,
        customers=customers,
        selected_customer_id=selected_customer_id,
        selected_zones=assigned_zone_ids,
        housesoldpriceaverage={},
        LOCATIONS=[]
    )


@zones_bp.route('/api/customer/<int:customer_id>/zones', methods=['GET'])
def api_get_customer_zones(customer_id):
    """
    Return the list of zone_ids assigned to this customer.
    """
    assigned_zone_ids = customerzonecontroller.get_customer_zone_ids(customer_id)
    return jsonify({"zone_ids": assigned_zone_ids})


@zones_bp.route('/api/customer/<int:customer_id>/zones', methods=['POST'])
def api_set_customer_zones(customer_id):
    """
    Replace this customer's zone assignments with the zone_ids from the request body.
    Expects JSON: { "zone_ids": [511, 204, ...] }
    """
    data = request.get_json() or {}
    zone_ids = data.get("zone_ids", [])

    cleaned_ids = customerzonecontroller.set_customer_zone_ids(customer_id, zone_ids)

    return jsonify({"status": "ok", "zone_ids": cleaned_ids})