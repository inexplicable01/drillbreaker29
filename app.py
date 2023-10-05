from flask import jsonify,Flask, render_template_string, redirect, url_for,request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
# from flask import g
from SMTP_email import send_email
import os
from werkzeug.utils import secure_filename
import csv
from ZillowSearch import loadcsv
# Define your database model


db = SQLAlchemy()
# Ensure the upload folder exists


def create_app(config_object="config.module.path"):
    app = Flask(__name__)

    # Apply config or any other settings
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///listings.db'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    # Initialize extensions with app
    db.init_app(app)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Optionally, you can use Flask's app context to create the tables.
    # However, this is generally done outside the create_app to allow more control over when tables are created.
    with app.app_context():
        db.create_all()

    # Register routes
    @app.route('/')
    def index():
        # Render an HTML template with a button
        return render_template_string("""
            <h1>Hello World</h1>
            <form action="{{ url_for('send_test_email') }}" method="post">
                <button type="submit">Send Test Email</button>
            </form>
        """)

    @app.route('/send-email', methods=['POST'])
    def send_test_email():
        # Use a subset of your listings or dummy data for testing
        test_listings = [{'id': 1,
                'details':'asdfasdf'},
                {'id': 2,
                'details':'tyjkhggg'}]

        email_content = "New Listings:\n"
        for listing in test_listings:
            email_content += f"ID: {listing['id']}, Details: {listing['details']}\n"
        send_email('New Listing', email_content)
        return redirect(url_for('index'))

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_csv():
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                import_csv_to_db(filepath)
                flash('CSV imported successfully!')
                return redirect(url_for('index'))

        return render_template_string("""
            <h1>Upload CSV</h1>
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="Upload">
            </form>
        """)

    @app.route('/beaman', methods=['GET', 'POST'])
    def searchdb():
        zillowdata = loadcsv()
        return render_template_string("""
            <h1>CSV Data</h1>
            <table border="1">
                <thead>
                    {% for key in data[0].keys() %}
                        <th>{{ key }}</th>
                    {% endfor %}
                </thead>
                <tbody>
                    {% for row in data %}
                        <tr>
                            {% for value in row.values() %}
                                <td>{{ value }}</td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        """, data=zillowdata)


    def import_csv_to_db(filepath):
        with open(filepath, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # skip header
            for row in csv_reader:
                listing = Listing(api_id=row[0], added_on=row[1])  # Adjust according to your CSV and model structure
                db.session.add(listing)
            db.session.commit()

    return app

# Define your database model outside of create_app so it's globally available
class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.String(50), unique=True, nullable=False)
    added_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

def check_new_listings():
    # Placeholder for your API check
    # api_url = "YOUR_REAL_ESTATE_API_URL"
    # response = requests.get(api_url)
    # data = response.json()
    # new_listings = []

    # for listing in data:
    #     if not Listing.query.filter_by(api_id=listing['id']).first():
    #         new_listing = Listing(api_id=listing['id'])
    #         db.session.add(new_listing)
    #         new_listings.append(listing)
    #
    # db.session.commit()
    #
    # if new_listings:
    test_listings = [{'id': 1,
            'details':'asdfasdf'},
            {'id': 2,
            'details':'tyjkhggg'}]

    email_content = "Scheduled New Listings:\n"
    for listing in test_listings:
        email_content += f"ID: {listing['id']}, Details: {listing['details']}\n"
    send_email('New Listing', email_content)




# if __name__ == '__main__':
app = create_app()
# scheduler = BackgroundScheduler()
# scheduler.add_job(func=check_new_listings, trigger="interval", minutes=1)
# scheduler.start()
    # app.run()
