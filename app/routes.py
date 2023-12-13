from flask import Blueprint, render_template,jsonify, redirect, url_for, request

from SMTP_email import send_email
# import os
# from werkzeug.utils import secure_filename
# import csv
from app.ZillowSearch import UpdateListfromLocation, SearchNewListing,SearchNewSoldHomes,SearchProperty
from app.ZillowDataProcessor import PicturesFromMLS
from app.HeatMapProcessing import *
import folium
main = Blueprint('main', __name__)
# from extensions import dbmethods
from app.DataBaseFunc import dbmethods
from app.NewListing import NewListing

# Register routes
@main.route('/')
def index():
    # Render an HTML template with a button
    return render_template('LandingPage.html')

@main.route('/send-email', methods=['POST'])
def send_test_email():
    # Use a subset of your listings or dummy data for testing
    test_listings = [{'id': 1,
                      'details': 'Can you see this'},
                     {'id': 2,
                      'details': 'tyjkhggg'}]

    email_content = "New Listings:\n"
    for listing in test_listings:
        email_content += f"ID: {listing['id']}, Details: {listing['details']}\n"
    # main.logger.error('wtf')
    # raise('problem')
    send_email('New Listing', email_content)
    # main.logger.error('got to here')
    return redirect(url_for('main.index'))

@main.route('/mapexample')
def MapExample():
    # Create a map
    m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)
    folium.Marker([45.5236, -122.6750], tooltip='Click me!', popup='Portland, OR').add_to(m)
    m = m._repr_html_()
    return render_template('MapTest.html', m=m)


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

@main.route('/showdb')
def showtable():
    # Use a subset of your listings or dummy data for testing
    listings = UpdateListfromLocation('Bellevue')
    return render_template('table_template.html', listings=listings)

@main.route('/newlistings')
def newlistings():
    # Use a subset of your listings or dummy data for testing
    SearchNewListing('Bellevue')
    SearchNewListing('Kenmore')
    SearchNewListing('Bothell')
    SearchNewListing('Kirkland')
    # UpdateListfromLocation('Bellevue', Listing, db)
    listings = dbmethods.ActiveListings()
    return render_template('table_template.html', listings=listings)

AreasToCareAbout =['Bellevue', 'Kenmore', 'Bothell' ,'Kirkland' ,'Seattle', 'Shoreline' ,'Renton', 'Kent' ,'Mercer' ,'Island']
@main.route('/allthesoldhomes')
def AllSoldHomes():
    # Use a subset of your listings or dummy data for testing
    # SearchNewSoldHomes('Bellevue')'Kenmore')('Bothell')('Kirkland')('Ballard')('Fremont')('Phinney Ridge')('Wallingford')'Shoreline')('Renton', "12m")
    # SearchNewSoldHomes('Clyde Hill', "12m")
    SearchNewSoldHomes('Medina', "12m")
    # SearchNewSoldHomes('Mercer Island', "12m")('Seattle', "12m")
    # UpdateListfromLocation('Bellevue', Listing, db)

    listings = dbmethods.AllListingsByDate()
    return render_template('table_template.html', listings=listings)

@main.route('/abunchofBellevueAddress')
def SomeBellevueAddress():
    addresses = dbmethods.AllBellevueAddress()
    return render_template('table_address_template.html', addresses=addresses)


@main.route('/beaman', methods=['GET', 'POST'])
def searchdb():
    listings = dbmethods.AllListigs()
    # for soldhouse in listings:
    #     listinglengthdays = ListingLength(soldhouse, Listing, db)
    return render_template('table_template.html', listings=listings)


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


@main.route('/givemecomps', methods=['GET','POST'])
def GiveMeComps():
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
    # if request.method == 'POST':
    #     ref_number = request.form.get('ref_number')
    #     success = PicturesFromMLS(ref_number)
    #     if success:  # Check if API was called successfully
    #         return jsonify(status="success", message="API called successfully")
    #     else:
    #         return jsonify(status="error", message="API call failed")
    maphtml = WaterFrontProperties()
    return render_template('SimpleMap.html',m=maphtml)
@main.route('/errormap', methods=['GET','POST'])
def errormap():
    # if request.method == 'POST':
    #     ref_number = request.form.get('ref_number')
    #     success = PicturesFromMLS(ref_number)
    #     if success:  # Check if API was called successfully
    #         return jsonify(status="success", message="API called successfully")
    #     else:
    #         return jsonify(status="error", message="API call failed")
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

@main.route('/mappotentialValue', methods=['GET', 'POST','PUT'])
def MapPotentialValue():
    # addresses = ["Address 1", "Address 2", "Address 3"]

    if request.method =='POST':
        days = 60
        description = request.form['description']
        # displayfun = request.form['displayfun']

        map_html2 = validateHomePredictionPrice2(description)
        return jsonify({'map_html2': map_html2, 'report': "Future Justification of Value"})
    elif request.method =='PUT':
        buildpotentiallowerlimit = request.form['buildpotentiallowerlimit']
        map_html, nu_hits = alladdresseswithbuilthomecalues(float(buildpotentiallowerlimit))
        return jsonify({'map_html': map_html, 'buildpotentiallowerlimit': buildpotentiallowerlimit, 'nu_hits':nu_hits})
    else:
        description = None
        buildpotentiallowerlimit=2000000
        averagenewbuildprice = None
        map_html2 = 'Display for Property details'
        # displayfun = SOLDHOTTNESS
    map_html, nu_hits = alladdresseswithbuilthomecalues(buildpotentiallowerlimit)

    return render_template('MapPotentialValue.html', map=map_html ,map2=map_html2,  description = description, buildpotentiallowerlimit=buildpotentiallowerlimit, nu_hits=nu_hits)


    # if request.method == 'POST':
    #     ref_number = request.form.get('ref_number')
    #     success = PicturesFromMLS(ref_number, Listing, db)
    #     if success:  # Check if API was called successfully
    #         return jsonify(status="success", message="API called successfully")
    #     else:
    #         return jsonify(status="error", message="API call failed")
    # return render_template('MLS_Input.html')


@main.route('/comparison_base', methods=['GET','POST'])
def comparison_base():
    # addresses = ["Address 1", "Address 2", "Address 3"]
    threeaddress = dbmethods.threeaddress()

    id = 0
    infodump=[]
    for address in threeaddress:
        images = []
        for photo in address.photos:
            for jpeg in photo['mixedSources']['jpeg']:
                if jpeg['width']==384:
                    images.append({
                        "url": jpeg['url'], "caption": photo['caption']
                    })
        infodump.append((address,f"carid{str(id)}", images))
        id = id +1


    return render_template('comparison_base.html', infodump=infodump)



@main.route('/new_listing', methods=['GET','POST'])
def new_listing():
    listings,infodump = NewListing(request)
    return render_template('NewListing.html', listings=listings, infodump=infodump)