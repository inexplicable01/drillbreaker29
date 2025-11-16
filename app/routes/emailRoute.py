# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, request, current_app
from app.RouteModel.EmailModel import (sendEmailwithNewListing,sendAppointmentEmail,sendEmailtimecheck,
                                       sendEmailpending)
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple


from werkzeug.exceptions import BadRequest

REQUIRED_FIELDS = {"email"}  # add more if your template absolutely needs them




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

@email_bp.route('/email_healthcheck', methods=['POST'])
def sendEmailHealthCheck():
    data = request.get_json(silent=True) or {}
    message = data.get('message')
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


# Single send (keeps legacy flow; now accepts JSON or form)


# Cron/Task: send everyone who is due (cadence)
@email_bp.route("/tasks/send-due", methods=["POST"])
def send_due():
    token = request.headers.get("X-Task-Token")
    expected = current_app.config.get("TASK_TOKEN")
    if expected and token != expected:
        return jsonify({"error": "unauthorized"}), 401

    now_utc = datetime.utcnow()
    due_customers = (
        Customer.query
        .filter(
            Customer.dontemail.is_(False),
            Customer.paused.is_(False),
            Customer.next_email_due_at.isnot(None),
            Customer.next_email_due_at <= now_utc,
        )
        .order_by(Customer.next_email_due_at.asc())
        .limit(500)
        .all()
    )

    processed = 0
    sent = 0
    for c in due_customers:
        # Shape the payload to what your template expects
        payload = {
            "id": str(c.id),
            "email": c.email or "",
            "name": c.name or "",
            "lastname": c.lastname or "",
            "phone": c.phone or "",
            "last_contacted": c.last_email_sent_at.strftime("%Y-%m-%d %H:%M:%S") if c.last_email_sent_at else "",
            # add any optional marketing fields you use:
            # "price_range": c.price_range or "",
            # "square_footage": c.square_footage or "",
        }

        ok, _ = _send_one(payload)
        processed += 1
        if ok:
            sent += 1
            c.last_email_sent_at = now_utc
            c.next_email_due_at = now_utc + timedelta(days=int(c.email_cadence_days or 14))
        else:
            # simple backoff so we don't re-try immediately forever
            c.next_email_due_at = now_utc + timedelta(days=1)

    db.session.commit()
    return jsonify({"processed": processed, "sent": sent, "now_utc": now_utc.isoformat()})


# Quick peek at who is due (GET)
@email_bp.route("/tasks/preview-due", methods=["GET"])
def preview_due():
    now_utc = datetime.utcnow()
    rows = (Customer.query
            .filter(
                Customer.dontemail.is_(False),
                Customer.paused.is_(False),
                Customer.next_email_due_at.isnot(None),
                Customer.next_email_due_at <= now_utc,
            )
            .order_by(Customer.next_email_due_at.asc())
            .limit(50)
            .all())
    return jsonify([
        {
            "id": c.id,
            "email": c.email,
            "cadence_days": c.email_cadence_days,
            "last_email_sent_at": c.last_email_sent_at.isoformat() if c.last_email_sent_at else None,
            "next_email_due_at": c.next_email_due_at.isoformat() if c.next_email_due_at else None
        } for c in rows
    ])
