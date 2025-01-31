from app.DBModels.SeattleNeighbourhoods import SeattleNeighbourhoods

from sqlalchemy.sql import func
from app.extensions import db
from datetime import datetime, timedelta
from app.config import Config
import pytz

class SeattleNeighbourhoodsController:
    def __init__(self):
        self.db = db
        self.SeattleNeighbourhoods = SeattleNeighbourhoods


    def getlist(self):

        SeattleNeighbourhoods = self.SeattleNeighbourhoods.query.all()
        return SeattleNeighbourhoods

seattleneighbourhoodcontroller = SeattleNeighbourhoodsController()
