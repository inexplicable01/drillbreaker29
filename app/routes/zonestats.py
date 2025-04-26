# email_bp.py
from datetime import datetime
import pytz
from app.DBFunc.ZoneStatsCacheController import zonestatscachecontroller
from flask import Blueprint, render_template, redirect, url_for, request,jsonify
# from app.RouteModel.EmailModel import sendEmailwithNewListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.config import Config,SW
zonestats_bp = Blueprint('zonestats_interesting', __name__, url_prefix='/zonestats')
from app.DBFunc.WashingtonCitiesController import washingtoncitiescontroller
from app.DBFunc.WashingtonZonesController import   washingtonzonescontroller
from app.MapTools.MappingTools import WA_geojson_features
from app.config import RECENTLYSOLD, FOR_SALE, PENDING
from app.GraphTools.plt_plots import *

@zonestats_bp.route('/basics', methods=['GET','POST'])
def zonestats():
    # Fetch precomputed city stats from the cache
    zonesdata = zonestatscachecontroller.get_all_zone_stats()
    seattle_tz = pytz.timezone('America/Los_Angeles')
    # Convert the cached data to a format suitable for rendering in the template
    formatted_data = [
        {
            'name': zone.zone.zonename(),
            'sold': zone.sold,
            'sold7_SFH': zone.sold7_SFH,
            'sold7_TCA': zone.sold7_TCA,
            'pending': zone.pending,
            'pending7_SFH': zone.pending7_SFH,
            'pending7_TCA': zone.pending7_TCA,
            'pending1': zone.pending1,
            'forsale': zone.forsale,
            'forsaleadded7_SFH': zone.forsaleadded7_SFH,
            'forsaleadded7_TCA': zone.forsaleadded7_TCA,
            'updated': zone.updated_time.astimezone(seattle_tz).strftime(
                '%m/%d/%Y %I:%M %p %A') if zone.updated_time else "N/A"
        }
        for zone in zonesdata
    ]

    return render_template('TransactionTable.html', citiesdata=formatted_data)


@zonestats_bp.route('/update', methods=['POST'])
def update_zone_stats():
    try:
        # cities = washingtoncitiescontroller.getallcities()
        zones =washingtonzonescontroller.getlist()
        zonestatscachecontroller.refresh_zone_stats(zones)
        return jsonify({"status": "success", "message": "City stats updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@zonestats_bp.route('/monthlytrends', methods=['GET','POST'])
def monthlytrends():
    # Fetch precomputed city stats from the cache
    plottingoptions = Config.plottingoptions
    # AllNeighbourhoods = featureAreas.keys()
    if request.method == 'POST':
        selectedhometypes = request.form.getlist('home_type')
        selectedlocations = request.form.getlist('location')
        selected_plotoption = request.form.get('selected_plotoption')

        selected_zones = request.form.getlist('selected_zones')
        if ',' in selected_zones[0]:
            selected_zones = selected_zones[0].split(',')

        # Process the selections as needed
    elif request.method == 'GET':
        selectedlocations = []
        selectedhometypes = Config.HOMETYPES
        selected_plotoption = plottingoptions[0]
        selected_zones = []

    zone_ids=[]
    for zonename in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zonename)
        if wzone:
            zone_ids.append(wzone.id)
    # soldhomes = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD, soldlastdays, selectedhometypes).all()
    results = brieflistingcontroller.getListingsByMonth(zone_ids, selectedhometypes, RECENTLYSOLD, selected_plotoption)
    chart_data = createBarGraph(results, f"Homes {selected_plotoption}", f"Homes {selected_plotoption} by Month (Zones {', '.join(map(str, zone_ids))})")

    results2 = brieflistingcontroller.getListingsByMonth(zone_ids, selectedhometypes, RECENTLYSOLD, "listed")
    chart_data2 = createBarGraph(results2, "Homes Listed", f"Homes Listed by Month (Zones {', '.join(map(str, zone_ids))})")


    return render_template(
        'MonthlyHTML/ClickAbleMap_Monthly.html',
        HOMETYPES=Config.HOMETYPES,
        geojson_features=WA_geojson_features,
        housesoldpriceaverage=[],
        plottingoptions=plottingoptions,
        selected_plotoption=selected_plotoption,
        selected_zones=selected_zones,
        selectedhometypes=selectedhometypes,
        LOCATIONS=[],
        selected_locations=selectedlocations,
        plot_url=chart_data,
        plot_url2=chart_data2,
        # plot_url2=plot_url2,
        soldhouses=[],
        brieflistings_SoldHomes_dict=[]
    )


@zonestats_bp.route('/update_graph', methods=['GET','POST'])
def update_graph():

    return render_template(
        'AreaReport2.html'
    )
