from flask import Blueprint, render_template,jsonify, redirect, url_for, request
from app.RouteModel.AreaReportModel import AreaReportModelRun,AreaReportModelRunForSale
from app.config import Config,SW
from app.MapTools.MappingTools import WA_geojson_features, featureAreas
soldhomes_bp = Blueprint('soldhomes_bp', __name__,url_prefix='/soldhomes')
from app.GraphTools.plt_plots import *


# @soldhomes_bp.route('/update-graph', methods=['POST'])
# def update_graph():
#     # Extract parameters from the request
#     selectedhometypes = request.form.getlist('home_type')
#     selectedlocations = request.form.getlist('location')
#
#     # Generate the new graph based on the parameters
#     # _, _, _, plot_url, new_plot_url = AreaReport(selectedlocations, selectedhometypes)
#     plot_url = displayModel(selectedlocations, selectedhometypes)
#     # Return the new graph data
#     return jsonify({'new_plot_url': plot_url})

# @soldhomes_bp.route('/areareport', methods=['GET','POST','PATCH'])
# def AreaReport():
#
#     doz_options = Config.doz_options
#     AllNeighbourhoods = featureAreas.keys()
#     if request.method == 'POST':
#         selectedhometypes = request.form.getlist('home_type')
#         selectedlocations = request.form.getlist('location')
#         selected_doz = int(request.form.get('selected_doz'))
#         # Process the selections as needed
#     elif request.method == 'GET':
#         selectedlocations = []
#         selectedhometypes = Config.HOMETYPES
#         selected_doz = 30
#
#
#
#
#     map_html,soldhouses, housesoldpriceaverage, plot_url,plot_url2 =AreaReportModelRun(selectedlocations, selectedhometypes,selected_doz)
#     # send_emailforOpenHouse(filtered_houses)
#     return render_template('AreaReport.html',
#                            m=map_html,
#                            HOMETYPES=Config.HOMETYPES,
#                            doz_options=doz_options,
#                            selected_doz=selected_doz,
#                            selectedhometypes= selectedhometypes,
#                            LOCATIONS=AllNeighbourhoods,
#                            soldhouses = soldhouses,
#                            housesoldpriceaverage=housesoldpriceaverage,
#                            selected_locations=selectedlocations,
#                            plot_url=plot_url,
#                            plot_url2=plot_url2)

from random import randint
@soldhomes_bp.route('/areareport', methods=['GET','POST','PATCH'])
def AreaReport():

    doz_options = Config.doz_options
    # AllNeighbourhoods = featureAreas.keys()
    if request.method == 'POST':
        selectedhometypes = request.form.getlist('home_type')
        selectedlocations = request.form.getlist('location')
        selected_doz = int(request.form.get('selected_doz'))

        selected_zones= request.form.getlist('selected_zones')
        if ',' in selected_zones[0]:
            selected_zones=selected_zones[0].split(',')

        # Process the selections as needed
    elif request.method == 'GET':
        selectedlocations = []
        selectedhometypes = Config.HOMETYPES
        selected_doz = 30
        selected_zones=[]

    housesoldpriceaverage, soldhomes=AreaReportModelRun(selected_zones, selectedhometypes,selected_doz)
    plot_url = createPriceChangevsDays2PendingPlot(soldhomes)
    plot_url2= createPricevsDays2PendingPlot(soldhomes)
    brieflistings_SoldHomes_dict=[]
    for brieflisting in soldhomes:
        if brieflisting.fsbo_status is None: # don't want to include fsbos cause it causes an error
            # hard code out for now.
            brieflistings_SoldHomes_dict.append(
               brieflisting.to_dict()
            )
    return render_template(
        'ClickAbleMap/ClickAbleMapMain.html',
                           HOMETYPES=Config.HOMETYPES,
                           geojson_features=WA_geojson_features,
                           housesoldpriceaverage=housesoldpriceaverage,
                           doz_options=doz_options,
                           selected_doz=selected_doz,
                           selected_zones=selected_zones,
                           selectedhometypes=selectedhometypes,
                           LOCATIONS=[],
                           selected_locations=selectedlocations,
                           plot_url=plot_url,
                           plot_url2=plot_url2,
                           soldhouses=soldhomes,
                        brieflistings_SoldHomes_dict=brieflistings_SoldHomes_dict
                           )

@soldhomes_bp.route('/areareportforsale', methods=['GET', 'POST', 'PATCH'])
def AreaReportFor_sale():

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

    housesoldpriceaverage,  forsalebrieflistings = AreaReportModelRunForSale(selected_zones, selectedhometypes,
                                                                               selected_doz)
    brieflistings_forsale_dict = []
    for brieflisting in forsalebrieflistings:
        if brieflisting.fsbo_status is None:  # don't want to include fsbos cause it causes an error
            # hard code out for now.
            brieflistings_forsale_dict.append(
                brieflisting.to_dict()
            )
    return render_template(
        'ClickAbleMap/ClickAbleMapMain.html',
        HOMETYPES=Config.HOMETYPES,
        geojson_features=WA_geojson_features,
        housesoldpriceaverage=housesoldpriceaverage,
        doz_options=doz_options,
        selected_doz=selected_doz,
        selected_zones=selected_zones,
        selectedhometypes=selectedhometypes,
        LOCATIONS=[],
        selected_locations=selectedlocations,
        # plot_url=plot_url,
        # plot_url2=plot_url2,
        soldhouses=forsalebrieflistings,
        brieflistings_SoldHomes_dict=brieflistings_forsale_dict
    )

                           # soldhouses = soldhouses,
                           # housesoldpriceaverage=housesoldpriceaverage,
                           # selected_locations=selectedlocations,
                           # plot_url=plot_url,
                           # plot_url2=plot_url2)