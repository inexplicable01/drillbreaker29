from flask import Blueprint, render_template,jsonify, redirect, url_for, request



# import os
# from werkzeug.utils import secure_filename
# import csv
# from flask import current_app as app
from app.ZillowAPI.ZillowDataProcessor import PicturesFromMLS
from app.HeatMapProcessing import *
import folium
main = Blueprint('main', __name__)
# from extensions import dbmethods
from app.DataBaseFunc import dbmethods
from app.NewListing import NewListing
from app.RouteModel.NewListingModel import NewListingInNeighbourhoods
from app.RouteModel.OldHousesModel import WhereOldBuild



@main.route('/mapexample')
def MapExample():
    # Create a map
    m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)
    folium.Marker([45.5236, -122.6750], tooltip='Click me!', popup='Portland, OR').add_to(m)
    m = m._repr_html_()
    return render_template('MapTest.html', m=m)





@main.route('/new_listing', methods=['GET','POST'])
def new_listing():
    # addresses = ["Address 1", "Address 2", "Address 3"]
    if request.method == 'POST':
        bedrooms = request.form.get('bedrooms')
        bathrooms = request.form.get('bathrooms')
        living_space = request.form.get('livingSpace')
        location = request.form.get('location')
        daysonzillow = request.form.get('daysonzillow')
    elif request.method == 'GET':
        bedrooms = 5
        bathrooms = 5
        living_space = 4000
        location = 'Seattle'
        daysonzillow = 1
    listings,infodump = NewListing(location,daysonzillow,bedrooms,bathrooms,living_space, )
    return render_template('NewListing.html', listings=listings, infodump=infodump,
                           bedrooms=bedrooms,bathrooms=bathrooms,living_space=living_space)

@main.route('/new_listing_in_selectneighbourhood', methods=['GET','POST'])
def new_listing_in_selectneighbourhood():
    # addresses = ["Address 1", "Address 2", "Address 3"]
    if request.method == 'POST':
        bedrooms = request.form.get('bedrooms')
        bathrooms = request.form.get('bathrooms')
        living_space = request.form.get('livingSpace')
        location = request.form.get('location')
        daysonzillow = request.form.get('daysonzillow')
    elif request.method == 'GET':
        bedrooms = 5
        bathrooms = 5
        living_space = 4000
        location = 'Seattle'
        daysonzillow = 1

    listings,infodump = NewListingInNeighbourhoods(location,daysonzillow,
                                                   bedrooms,bathrooms,
                                                   living_space)
    return render_template('NewListing.html', listings=listings, infodump=infodump,
                           bedrooms=bedrooms,bathrooms=bathrooms,living_space=living_space)


@main.route('/heatmapexample', methods=['GET', 'POST'])
def HeatMapExample():
    if request.method =='POST':
        days = int(request.form['days'])
        displayfun = request.form['displayfun']
    else:
        days = 90
        displayfun = SOLDHOTTNESS
    m,lenresults = HeatMapGen(days,displayfun)
    return render_template('MapTest.html', m=m, selected_days=days, displayfun=displayfun , lenresults=lenresults)
    # Create a map

@main.route('/wheretobuild', methods=['GET', 'POST'])
def WhereToBuild():
    if request.method =='POST':
        days = 60
        minprice= int(request.form['minprice'])
        # displayfun = request.form['displayfun']
    else:
        days = 60
        minprice = 2000000
        # displayfun = SOLDHOTTNESS
    m = highvalueMap()
    return render_template('WhereToBuild.html', m=m, minprice=minprice, days=days)


# @main.route('/newlistings')
# def newlistings():
#     # Use a subset of your listings or dummy data for testing

#
#     listings = dbmethods.ActiveListings()
#     return render_template('table_template.html', listings=listings)

# AreasToCareAbout =['Bellevue', 'Kenmore', 'Bothell' ,'Kirkland' ,'Seattle', 'Shoreline' ,'Renton', 'Kent' ,'Mercer' ,'Island']


# @main.route('/abunchofBellevueAddress')
# def SomeBellevueAddress():
#     addresses = dbmethods.AllBellevueAddress()
#     return render_template('table_address_template.html', addresses=addresses)


# @main.route('/beaman', methods=['GET', 'POST'])
# def searchdb():
#     listings = dbmethods.AllListigs()
#     # for soldhouse in listings:
#     #     listinglengthdays = ListingLength(soldhouse, Listing, db)
#     return render_template('table_template.html', listings=listings)


@main.route('/downloadpicsfromMLS', methods=['GET','POST'])
def download_pics():
    if request.method == 'POST':
        ref_number = request.form.get('ref_number')
        success = PicturesFromMLS(ref_number)
        if success:  # Check if API was called successfully
            return jsonify(status="success", message="API called successfully")
        else:
            return jsonify(status="error", message="API call failed")
    return render_template('MLS_Input.html')

@main.route('/waterfrontproperties', methods=['GET','POST'])
def waterfrontproperties():
    maphtml = WaterFrontProperties()
    return render_template('SimpleMap.html',m=maphtml)
@main.route('/errormap', methods=['GET','POST'])
def errormap():
    maphtml = PredictionError()
    return render_template('SimpleMap.html',m=maphtml)
@main.route('/newbuildlocations', methods=['GET','POST'])
def GiveMeComps2():
    # addresses = ["Address 1", "Address 2", "Address 3"]
    if request.method =='POST':
        days = 60
        selected_address = request.form.get('address')
        # displayfun = request.form['displayfun']
    else:

        selected_address = None
        averagenewbuildprice = None
        # displayfun = SOLDHOTTNESS
    m = WhereNewBuild()
    m2, addressestoclick, averagenewbuildprice = WhereOldBuild(selected_address)

    return render_template('WhereToBuild.html', m=m, m2=m2,
                           addresses=addressestoclick,
                           selected_address=selected_address,
                           averagenewbuildprice=averagenewbuildprice)