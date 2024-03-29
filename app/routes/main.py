# email_bp.py
from flask import Blueprint, redirect, url_for,render_template
from app.RouteModel.EmailModel import sendEmailwithNewListing

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Render an HTML template with a button
    return render_template('LandingPage.html')