from flask import Flask, render_template_string, redirect, url_for,request, flash
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()
# Ensure the upload folder exists
from app.models import Listing
from .routes import main
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from SMTP_email import send_emailstatic

mail = Mail()
scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(func=send_emailstatic, trigger="interval", minutes=1)
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

def create_app(debug=False,config_object="config.module.path"):
    app = Flask(__name__, instance_relative_config=True)


    # Apply config or any other settings
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'listings.db')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.debug=debug

    # Initialize extensions with app
    db.init_app(app)


    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Optionally, you can use Flask's app context to create the tables.
    # However, this is generally done outside the create_app to allow more control over when tables are created.
    with app.app_context():
        db.create_all()


    # mail.init_app(app)

    # if not app.debug or os.environ.get('FLASK_RUN_FROM_CLI') != 'true':
    #     start_scheduler()

    # def import_csv_to_db(filepath):
    #     with open(filepath, 'r') as file:
    #         csv_reader = csv.reader(file)
    #         next(csv_reader)  # skip header
    #         for row in csv_reader:
    #             listing = Listing(api_id=row[0], added_on=row[1])  # Adjust according to your CSV and model structure
    #             db.session.add(listing)
    #         db.session.commit()

    app.register_blueprint(main)
    return app