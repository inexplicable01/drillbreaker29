# email_bp.py
from flask import Blueprint, redirect, url_for
from app.RouteModel.EmailModel import sendEmailwithNewListing

email_bp = Blueprint('email', __name__, url_prefix='/email')

# @email_bp.route('/send-test', methods=['POST'])
# def send_test_email():
#     # Use a subset of your listings or dummy data for testing
#     test_listings = [{'id': 1, 'details': 'Can you see this'},
#                      {'id': 2, 'details': 'tyjkhggg'}]
#
#     email_content = "New Listings:\n"
#     for listing in test_listings:
#         email_content += f"ID: {listing['id']}, Details: {listing['details']}\n"
#     # Assuming `send_email` is a function that actually sends the email.
#     # send_email('New Listing', email_content)
#     return redirect(url_for('main.index'))

@email_bp.route('/send-updates', methods=['POST'])
def sendEmailUpdates():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    sendEmailwithNewListing()
    return redirect(url_for('main.index'))
