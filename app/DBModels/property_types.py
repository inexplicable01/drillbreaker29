from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from app.extensions import db


class PropertyType(db.Model):
    __tablename__ = 'property_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)