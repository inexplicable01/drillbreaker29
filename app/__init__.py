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
from dotenv import load_dotenv
from os import getenv
from sshtunnel import SSHTunnelForwarder

load_dotenv()  # Load the environment variables from .env

mail = Mail()
scheduler = BackgroundScheduler()

def create_ssh_tunnel():
    server = SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
        remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
    )
    server.start()
    return server


# def configure_app(app, tunnel=None):
#     if tunnel:
#         local_bind_port = tunnel.local_bind_port
#         db_host = '127.0.0.1'
#     else:
#         db_host = os.getenv('DATABASE_HOST')
#
#     app.config['SQLALCHEMY_DATABASE_URI'] = (
#         f"mysql+mysqldb://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASS')}"
#         f"@{db_host}/{os.getenv('DATABASE_NAME')}"
#     )
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(func=send_emailstatic, trigger="interval", minutes=1)
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

def create_app(debug=False,config_object="config.module.path"):
    env = os.getenv('FLASK_ENV', 'production')
    app = Flask(__name__, instance_relative_config=True)
    tunnel = None

    if os.getenv('FLASK_ENV') == 'development':
        # Setup SSH tunnel in development
        tunnel = create_ssh_tunnel()
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqldb://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASS')}"
            f"@127.0.0.1:{tunnel.local_bind_port}/{os.getenv('DATABASE_NAME')}"
        )
    else:
        # Direct database connection in production
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqldb://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASS')}"
            f"@{os.getenv('DATABASE_HOST')}/{os.getenv('DATABASE_NAME')}"
        )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Apply config or any other settings
    # app.config['SQLALCHEMY_DATABASE_URI'] = (
    #     f"mysql+mysqldb://{getenv('DATABASE_USER')}:{getenv('DATABASE_PASS')}"
    #     f"@{getenv('DATABASE_HOST')}/{getenv('DATABASE_NAME')}"
    # )
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # to suppress a warning
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
    return app, tunnel