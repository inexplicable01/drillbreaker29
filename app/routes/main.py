# email_bp.py
from flask import Blueprint, redirect, url_for,render_template
from app.DBFunc.BriefListingController import brieflistingcontroller
from datetime import datetime
import pytz

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Render an HTML template with a button
    lastupdate= brieflistingcontroller.latestListingTime()
    seattle_tz = pytz.timezone('America/Los_Angeles')
    readable_time = datetime.fromtimestamp(lastupdate, tz=pytz.utc).astimezone(seattle_tz).strftime(
        '%m/ %d/ %Y   %I:%M %p %A')
    recent_pending_count = brieflistingcontroller.getListingsWithStatus(7,'PENDING').count()

    return render_template('LandingPage.html', lastupdate=readable_time, recent_pending_count=recent_pending_count)