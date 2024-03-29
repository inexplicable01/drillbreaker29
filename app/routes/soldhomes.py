from flask import Blueprint, render_template,jsonify, redirect, url_for, request
from app.RouteModel.AreaReportModel import displayModel,AreaReport,AreaReportGatherData,ListAllNeighhourhoodsByCities
from app.config import Config,SW
soldhomes_bp = Blueprint('soldhomes_bp', __name__,url_prefix='/soldhomes')
@soldhomes_bp.route('/update-graph', methods=['POST'])
def update_graph():
    # Extract parameters from the request
    selectedhometypes = request.form.getlist('home_type')
    selectedlocations = request.form.getlist('location')

    # Generate the new graph based on the parameters
    # _, _, _, plot_url, new_plot_url = AreaReport(selectedlocations, selectedhometypes)
    plot_url = displayModel(selectedlocations, selectedhometypes)
    # Return the new graph data
    return jsonify({'new_plot_url': plot_url})

@soldhomes_bp.route('/areareport', methods=['GET','POST','PATCH'])
def AreaReport():


    citiestoinspect = ['Seattle']
    AllNeighbourhoods = ListAllNeighhourhoodsByCities(citiestoinspect)
    if request.method == 'POST':
        selectedhometypes = request.form.getlist('home_type')
        selectedlocations = request.form.getlist('location')
        # Process the selections as needed
    elif request.method == 'GET':
        selectedlocations = []
        selectedhometypes = Config.HOMETYPES
    elif request.method == 'PATCH':
        try:

            AreaReportGatherData(citiestoinspect)
            # If the function successfully completes, return a success message
            return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
        except Exception as e:
            # If the function fails, return a failure message with details
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500



    map_html,soldhouses, housesoldpriceaverage, plot_url,plot_url2 =AreaReport(selectedlocations, selectedhometypes)
    # send_emailforOpenHouse(filtered_houses)
    return render_template('AreaReport.html',
                           m=map_html,
                           HOMETYPES=Config.HOMETYPES,
                           selectedhometypes= selectedhometypes,
                           LOCATIONS=AllNeighbourhoods,
                           soldhouses = soldhouses,
                           housesoldpriceaverage=housesoldpriceaverage,
                           selected_locations=selectedlocations,
                           plot_url=plot_url,
                           plot_url2=plot_url2)
