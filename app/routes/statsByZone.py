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


import io
@zonestats_bp.route('/monthlytrends', methods=['GET','POST'])
def monthlytrends():
    # Fetch precomputed city stats from the cache
    doz_options = Config.doz_options
    # AllNeighbourhoods = featureAreas.keys()
    if request.method == 'POST':
        selectedhometypes = request.form.getlist('home_type')
        selectedlocations = request.form.getlist('location')
        selected_doz = int(request.form.get('selected_doz'))

        selected_zones = request.form.getlist('selected_zones')
        if ',' in selected_zones[0]:
            selected_zones = selected_zones[0].split(',')

        # Process the selections as needed
    elif request.method == 'GET':
        selectedlocations = []
        selectedhometypes = Config.HOMETYPES
        selected_doz = 30
        selected_zones = []

    zone_ids=[]
    for zonename in selected_zones:
        wzone = washingtonzonescontroller.getzonebyName(zonename)
        if wzone:
            zone_ids.append(wzone.id)
    # soldhomes = brieflistingcontroller.listingsByZonesandStatus(zone_ids, RECENTLYSOLD, soldlastdays, selectedhometypes).all()
    results = brieflistingcontroller.getListingsByMonth(zone_ids, selectedhometypes, RECENTLYSOLD)
    data = {(year, month): count for year, month, count in results}
    # Unpack data
    today = datetime.now()
    months = [i for i in range(1, 13)]
    year1 = today.year - 2 if today.month < 12 else today.year - 1
    year2 = year1 + 1

    # Y-values for both years
    counts_year1 = [data.get((year1, m), 0) for m in months]
    counts_year2 = [data.get((year2, m), 0) for m in months]

    # Labels: Jan, Feb, ...
    month_labels = [datetime(2000, m, 1).strftime("%b") for m in months]

    # Plot using Matplotlib
    x = range(len(months))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([i - width/2 for i in x], counts_year1, width=width, label=str(year1), color='skyblue')
    ax.bar([i + width/2 for i in x], counts_year2, width=width, label=str(year2), color='salmon')

    ax.set_xticks(x)
    ax.set_xticklabels(month_labels)
    ax.set_xlabel("Month")
    ax.set_ylabel("Homes Sold")
    ax.set_title(f"Homes Sold by Month (Zones {', '.join(map(str, zone_ids))})")
    ax.legend()

    plt.tight_layout()

    # Convert to base64 image
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    plt.close(fig)


    return render_template(
        'ClickAbleMap/ClickAbleMapMain2.html',
        HOMETYPES=Config.HOMETYPES,
        geojson_features=WA_geojson_features,
        housesoldpriceaverage=[],
        doz_options=doz_options,
        selected_doz=selected_doz,
        selected_zones=selected_zones,
        selectedhometypes=selectedhometypes,
        LOCATIONS=[],
        selected_locations=selectedlocations,
        plot_url=chart_data,
        # plot_url2=plot_url2,
        soldhouses=[],
        brieflistings_SoldHomes_dict=[]
    )


@zonestats_bp.route('/update_graph', methods=['GET','POST'])
def update_graph():

    return render_template(
        'AreaReport2.html'
    )
