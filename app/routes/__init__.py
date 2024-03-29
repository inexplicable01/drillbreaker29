from flask import Flask
# from .auth import auth_bp
from .openhouse import openhouse_bp
from .soldhomes import soldhomes_bp
from .email import email_bp
from .listingalerts import alert_bp
from .main import main

def register_blueprints(app: Flask):
    app.register_blueprint(alert_bp)
    app.register_blueprint(soldhomes_bp)
    app.register_blueprint(openhouse_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(main)
