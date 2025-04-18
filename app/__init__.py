from flask import Flask
import os
# Ensure the upload folder exists
# from app.models import Listing
from .routes import register_blueprints
from flask_mail import Mail, Message

import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from sshtunnel import SSHTunnelForwarder
# from app.DBModels.Listing import Listing,Base as dbBase
# load_dotenv()  # Load the environment variables from .env
# db = SQLAlchemy()
# from config import Config
# Function to load .env file manually
def load_env(env_file=".env"):
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Call the function to load the environment variables
load_env()

mail = Mail()
# scheduler = BackgroundScheduler()

def create_ssh_tunnel():
    try:
        server = SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username=os.getenv('SSH_USER'),
            ssh_password=os.getenv('SSH_PASS'),
            remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
        )
        server.start()
        return server
    except Exception as e:
        raise RuntimeError(f"SSH Tunnel Error: {e}")

# def create_ssh_tunnel():
#     server = SSHTunnelForwarder(
#         ('ssh.pythonanywhere.com'),
#         ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
#         remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306),
#         # banner_timeout=30  # Increase timeout
#     )
#     server.start()
#     return server




from app.extensions import db
# from app.DataBaseFunc import dbmethods

def create_app(debug=False,config_object="config.module.path"):
    app = Flask(__name__, instance_relative_config=True)
    tunnel = None
    # app.config.from_object(Config)
    if os.getenv('FLASK_ENV') == 'development':
        # Setup SSH tunnel in development
        tunnel = create_ssh_tunnel()
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 3600, 'pool_pre_ping': True}
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqldb://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASS')}"
            f"@127.0.0.1:{tunnel.local_bind_port}/{os.getenv('DATABASE_NAME')}"
        )

        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mylocaldatabase.db'
    else:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 3600, 'pool_pre_ping':True}
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqldb://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASS')}"
            f"@{os.getenv('DATABASE_HOST')}/{os.getenv('DATABASE_NAME')}"
        )
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mylocaldatabase.db'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    app.secret_key ='DAMNITWAYER'

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Optionally, you can use Flask's app context to create the tables.
    # However, this is generally done outside the create_app to allow more control over when tables are created.
    with app.app_context():
        from app.DBModels.BriefListing import BriefListing
        from app.DBModels.CustomerZpid import CustomerZpid

        # Register relationships (execute only after models are loaded)
        from app.DBModels import relationships
        db.create_all()

    register_blueprints(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    # dbmethods.db = db
    return app, tunnel


# def start_scheduler():
#     if not scheduler.running:
#         scheduler.add_job(func=send_emailstatic, trigger="interval", minutes=1)
#         scheduler.start()
#         atexit.register(lambda: scheduler.shutdown())