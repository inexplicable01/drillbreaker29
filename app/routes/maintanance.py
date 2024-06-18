# email_bp.py
from flask import Blueprint, redirect, url_for
from app.DBFunc.BriefListingController import brieflistingcontroller

maintanance_bp = Blueprint('maintanance_bp', __name__, url_prefix='/maintanance')


@maintanance_bp.route('/neighcleanup', methods=['POST'])
def neighcleanup():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    cleanupresults = brieflistingcontroller.listingsN_Cleanup()
    return cleanupresults, 200