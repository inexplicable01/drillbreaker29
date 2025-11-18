# email_bp.py
from flask import Blueprint, redirect, url_for, render_template, request, jsonify
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowByAddress  # <-- NEW IMPORT
from datetime import datetime
import pytz

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Render an HTML template with a button
    lastupdate = brieflistingcontroller.latestListingTime()
    seattle_tz = pytz.timezone('America/Los_Angeles')
    readable_time = datetime.fromtimestamp(lastupdate, tz=pytz.utc).astimezone(seattle_tz).strftime(
        '%m/ %d/ %Y   %I:%M %p %A')
    recent_pending_count = brieflistingcontroller.getListingsWithStatus(7, 'PENDING').count()

    return render_template('LandingPage.html',
                           lastupdate=readable_time,
                           recent_pending_count=recent_pending_count)


@main.route('/api/zillow/search_by_address', methods=['POST'])
def api_zillow_search_by_address():
    """
    JSON API for other frontends and the local tester.
    Expects JSON: { "address": "123 Main St, Seattle, WA 98101" }
    Returns Zillow (or proxy) JSON.
    """
    data = request.get_json(silent=True) or {}
    address = data.get("address")

    if not address:
        return jsonify({"error": "Missing 'address' in JSON body"}), 400

    try:
        result = SearchZillowByAddress(address)
    except Exception as e:
        # You can narrow this to requests.exceptions.RequestException if you want
        return jsonify({
            "error": "Upstream Zillow request failed",
            "details": str(e),
        }), 502

    return jsonify(result), 200
