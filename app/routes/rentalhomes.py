from flask import Blueprint, render_template,jsonify, redirect, url_for, request
from app.RouteModel.AreaReportModel import displayModel,AreaReportModelRun,AreaReportGatherData,ListAllNeighhourhoodsByCities
from app.config import Config,SW
rental_bp = Blueprint('rental_bp', __name__,url_prefix='/rentalhomes')
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.MapTools.MappingTools import generateMap
from app.ZillowAPI.ZillowDataProcessor import ListingLengthbyBriefListing, \
    loadPropertyDataFromBrief,FindHomesByNeighbourhood, ListingStatus
from app.ZillowAPI.ZillowAPICall import RentEstimateBriefListing



@rental_bp.route('/findgoodinvestment', methods=['GET','POST'])
def good_investment():
    # Extract parameters from the request
    # Generate the new graph based on the parameters
    # _, _, _, plot_url, new_plot_url = AreaReport(selectedlocations, selectedhometypes)
    AllNeighbourhoods = ListAllNeighhourhoodsByCities(Config.CITIES)
    if request.method == 'POST':
        selectedlocation = request.form.getlist('location')
        # Process the selections as needed
    elif request.method == 'GET':
        selectedlocation = 'Kirkland'
    listofforsalehomes= brieflistingcontroller.forSaleInCity(selectedlocation)
    rentablehomes=[]
    count = 1
    interestrate = 0.06/12
    loanlength =30*12
    print(f" Assume Interest Rate of {interestrate * 12}. Assume {loanlength / 12} years")
    for brieflist in listofforsalehomes:
        # print(brieflist.zpid)
        # print(brieflist.price)
        try:
            if brieflist.homeType not in ['CONDO','TOWNHOUSE']:
                continue
            if brieflist.rentZestimate != 0:
                mortgage = 0.75 * brieflist.price * (interestrate * (1 + interestrate) ** loanlength) / (
                            (1 + interestrate) ** (loanlength) - 1)


                propertydata = loadPropertyDataFromBrief(brieflist)
                hoafee=0
                if 'monthlyHoaFee' in propertydata.keys():
                    if type(propertydata['monthlyHoaFee']) is float or type(propertydata['monthlyHoaFee']) is int :
                        hoafee=propertydata['monthlyHoaFee']
                print(
                f"75% of listing price is {brieflist.price * 0.75}, mortgage on this is {mortgage}, tax is {brieflist.price * 0.008 / 12}, hoa is {hoafee}")
                cashflow = brieflist.rentZestimate - mortgage - brieflist.price * 0.008 / 12 - hoafee
                print(f"RentZestimate is {brieflist.rentZestimate}, monthly cashflow is {cashflow}")
                if cashflow>-100.0:
                    rentablehomes.append((brieflist, cashflow))
        except:
            print("error" + brieflist.streetAddress)
        # propertydata=loadPropertyDataFromBrief(brieflist)
        # print(propertydata)
        # try:
        #     # restimate = RentEstimateBriefListing(brieflist.streetAddress + ',' + brieflist.city)
        #     # print(restimate['data']['floorplans'][0]['zestimate']['rentZestimate'], brieflist.rentZestimate)
        #     # rentablehomes.append( (brieflist, restimate['data']['floorplans'][0]['zestimate']['rentZestimate'])  )
        # except:
        #     print(brieflist)
        # count+=1
        # # if count>10:
        # #     break


    ### get list of
    # send_emailforOpenHouse(filtered_houses)
    return render_template('MapplusTable.html',
                           m=generateMap(listofforsalehomes, None,None),
                           listings=rentablehomes,
                           LOCATIONS=AllNeighbourhoods,
                           selected_location=selectedlocation)

@rental_bp.route('/blah', methods=['GET','POST','PATCH'])
def blah():

    doz_options = Config.doz_options
    AllNeighbourhoods = ListAllNeighhourhoodsByCities(Config.CITIES)
    if request.method == 'POST':
        selectedhometypes = request.form.getlist('home_type')
        selectedlocations = request.form.getlist('location')
        selected_doz = int(request.form.get('selected_doz'))
        # Process the selections as needed
    elif request.method == 'GET':
        selectedlocations = []
        selectedhometypes = Config.HOMETYPES
        selected_doz = 30
    elif request.method == 'PATCH':
        try:
            selected_doz =  int(request.form.get('doz'))
            AreaReportGatherData(Config.CITIES,selected_doz)
            # If the function successfully completes, return a success message
            return jsonify({'status': 'success', 'message': 'Data gathering complete.'}), 200
        except Exception as e:
            # If the function fails, return a failure message with details
            return jsonify({'status': 'failure', 'message': 'Data gathering failed.', 'details': str(e)}), 500



    map_html,soldhouses, housesoldpriceaverage, plot_url,plot_url2 =AreaReportModelRun(selectedlocations, selectedhometypes,selected_doz)
    # send_emailforOpenHouse(filtered_houses)
    return render_template('AreaReport.html',
                           m=map_html,
                           HOMETYPES=Config.HOMETYPES,
                           doz_options=doz_options,
                           selected_doz=selected_doz,
                           selectedhometypes= selectedhometypes,
                           LOCATIONS=AllNeighbourhoods,
                           soldhouses = soldhouses,
                           housesoldpriceaverage=housesoldpriceaverage,
                           selected_locations=selectedlocations,
                           plot_url=plot_url,
                           plot_url2=plot_url2)
