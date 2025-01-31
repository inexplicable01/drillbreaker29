from flask import Flask
# from .auth import auth_bp
from .openhouse import openhouse_bp
from .soldhomes import soldhomes_bp
from .email import email_bp
from .listingalerts import alert_bp
from .main import main
from .hothomes import hothomes_bp
from .neighbourhoodreport import neighbourhoodreport_bp
from .maintanance import maintanance_bp
from .sellersupport import sellersupport_bp
from .clickablemap import clickablemap_bp
from .platformSMSsupport import platformSMSBP
from .email_monitor import emailmonitorbp
from .rentalhomes import rental_bp
from .fsbo import fsbo_bp
from .statsByCity import citystats_bp
from .customerInterestNeighbourhood import customer_interest_bp

def register_blueprints(app: Flask):
    app.register_blueprint(alert_bp)
    app.register_blueprint(soldhomes_bp)
    app.register_blueprint(openhouse_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(main)
    app.register_blueprint(hothomes_bp)
    app.register_blueprint(neighbourhoodreport_bp)
    app.register_blueprint(maintanance_bp)
    app.register_blueprint(sellersupport_bp)
    app.register_blueprint(clickablemap_bp)
    app.register_blueprint(platformSMSBP)
    app.register_blueprint(emailmonitorbp)
    app.register_blueprint(rental_bp)
    app.register_blueprint(fsbo_bp)
    app.register_blueprint(citystats_bp)
    app.register_blueprint(customer_interest_bp)