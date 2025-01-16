# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, request
from app.RouteModel.EmailModel import sendEmailwithNewListing,sendAppointmentEmail,sendEmailtimecheck, sendEmailpending

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

@email_bp.route('/email_healthcheck', methods=['GET'])
def sendEmailHealthCheck():
    # Retrieve the 'message' parameter from the request
    message = request.args.get('message')  # For GET requests, use args to get query parameters
    if not message:
        message = None
    sendEmailtimecheck(message)
    return jsonify({"message": "Viewing request submitted successfully!"}), 200

@email_bp.route('/email_pendingcheck', methods=['GET'])
def sendEmailPending():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    sendEmailpending()
    return jsonify({"message": "Viewing request submitted successfully!"}), 200

@email_bp.route('/scheduleviewing', methods=['POST'])
def schedulingemail():
    try:
        # Parse the incoming JSON data from the request
        data = request.get_json()

        # Log the incoming data to verify it
        print("Received Data:", data)  # Or use logging for production

        # Extract values from the request (optional, for logging purposes)
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        viewing_date = data.get('viewingDate')
        viewing_time = data.get('viewingTime')
        zpid = data.get('zpid')
        address = data.get('address')

        print(f"Name: {name}, Email: {email}, Phone: {phone}, Viewing Date: {viewing_date}, Viewing Time: {viewing_time}")
        sendAppointmentEmail(name,email,phone,viewing_date,viewing_time,zpid,address)
        # Assume sendEmailwithNewListing() is a function that sends the email
        # sendEmailwithNewListing(name, email, phone, viewing_date, viewing_time)

        # Respond with a success message in JSON format
        return jsonify({"message": "Viewing request submitted successfully!"}), 200
    except Exception as e:
        # Handle any errors and respond with a JSON error message
        print(f"Error: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 400

