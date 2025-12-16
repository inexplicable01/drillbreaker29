from flask import Blueprint, render_template,jsonify, redirect, url_for, request
# from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,AreaReportGatherData,ListAllNeighhourhoodsByCities
# from app.config import Config,SW
from app.RouteModel.OpenHouseModel import SearchForOpenHouses

openhouse_bp = Blueprint('openhouse', __name__,url_prefix='/openhouse')

@openhouse_bp.route('/showopenhouseopportunity', methods=['GET','POST'])
def SearchForOpenHouseRoute():
    map_html, openhouse_propertydata = SearchForOpenHouses()
    return render_template('OpenHouse.html', m=map_html)


