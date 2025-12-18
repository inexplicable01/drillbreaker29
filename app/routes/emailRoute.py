# email_bp.py
from flask import Blueprint, redirect, url_for, jsonify, request, current_app
from app.RouteModel.EmailModel import (sendAppointmentEmail,sendEmailtimecheck,
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
    # sendEmailwithNewListing()
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

@email_bp.route('/send_recommendation_summary', methods=['POST'])
def send_recommendation_summary():
    """
    Send final summary email after processing all customer recommendations.
    Called by Tasks_UpdateClientRecommendationThruAI.py
    """
    from app.RouteModel.EmailModel import send_email, defaultrecipient
    import pytz

    try:
        data = request.get_json()
        totals = data.get('totals', {})
        timestamp = data.get('timestamp', datetime.now().isoformat())

        seattle_tz = pytz.timezone('America/Los_Angeles')
        current_time = datetime.fromisoformat(timestamp).astimezone(seattle_tz)
        formatted_time = current_time.strftime('%B %d, %Y at %I:%M %p %Z')

        # Build customer details table if there are matches
        customer_details_html = ""
        if totals.get('customer_details'):
            customer_details_html = """
            <h3 style="color: #1a73e8; margin-top: 30px;">Customers with Matches:</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Customer</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">ID</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">High-Scoring (70+)</th>
                        <th style="padding: 10px; text-align: center; border: 1px solid #ddd;">Excellent (90+)</th>
                    </tr>
                </thead>
                <tbody>
            """
            for customer in totals['customer_details']:
                customer_details_html += f"""
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{customer['name']}</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">{customer['id']}</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: bold; color: #1a73e8;">{customer['high_scoring']}</td>
                        <td style="padding: 10px; text-align: center; border: 1px solid #ddd; font-weight: bold; color: #28a745;">{customer['excellent']}</td>
                    </tr>
                """
            customer_details_html += """
                </tbody>
            </table>
            """

        summary_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 700px;
                    margin: 20px auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 8px;
                }}
                h2 {{
                    color: #1a73e8;
                    margin-top: 0;
                    border-bottom: 3px solid #1a73e8;
                    padding-bottom: 10px;
                }}
                .stat-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    padding: 15px;
                    background-color: white;
                    border-left: 4px solid #1a73e8;
                    border-radius: 4px;
                }}
                .stat-card.excellent {{
                    border-left-color: #28a745;
                }}
                .stat-card.warning {{
                    border-left-color: #ffc107;
                }}
                .stat-card.error {{
                    border-left-color: #dc3545;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .stat-value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1a73e8;
                }}
                .stat-card.excellent .stat-value {{
                    color: #28a745;
                }}
                .stat-card.warning .stat-value {{
                    color: #ffc107;
                }}
                .stat-card.error .stat-value {{
                    color: #dc3545;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🎯 Customer Recommendation Run Complete</h2>
                <p><strong>Completed:</strong> {formatted_time}</p>

                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-label">Customers Processed</div>
                        <div class="stat-value">{totals.get('customers_processed', 0)}</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">Customers with Matches</div>
                        <div class="stat-value">{totals.get('customers_with_matches', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Listings Evaluated</div>
                        <div class="stat-value">{totals.get('total_evaluated', 0)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">High-Scoring Listings (70+)</div>
                        <div class="stat-value">{totals.get('total_high_scoring', 0)}</div>
                    </div>
                    <div class="stat-card excellent">
                        <div class="stat-label">Excellent Matches (90+)</div>
                        <div class="stat-value">{totals.get('total_excellent', 0)}</div>
                    </div>
                    <div class="stat-card {'error' if totals.get('errors', 0) > 0 else ''}">
                        <div class="stat-label">Errors</div>
                        <div class="stat-value">{totals.get('errors', 0)}</div>
                    </div>
                </div>

                {customer_details_html}

                <div class="footer">
                    <p>Wayber Real Estate Analytics - AI Recommendation System</p>
                    <p>This summary covers all customers processed in this batch</p>
                </div>
            </div>
        </body>
        </html>
        """

        send_email(
            subject=f"AI Recommendations Complete: {totals.get('customers_processed', 0)} customers, {totals.get('total_high_scoring', 0)} matches",
            html_content=summary_html,
            recipient=defaultrecipient
        )

        return jsonify({"status": "success", "message": "Summary email sent"}), 200

    except Exception as e:
        print(f"Error sending recommendation summary email: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500




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
