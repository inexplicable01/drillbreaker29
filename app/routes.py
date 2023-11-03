from flask import Blueprint, render_template,jsonify,render_template_string, redirect, url_for, request, flash
from . import db
from .models import Listing
from SMTP_email import send_email
# import os
# from werkzeug.utils import secure_filename
# import csv
from ZillowSearch import loadcsv,UpdateListfromLocation, SearchNewListing,SearchNewSoldHomes
from ZillowDataProcessor import ListingLength, PicturesFromMLS
from app.HeatMapProcessing import HeatMapGen, SOLDHOTTNESS,EXPENSIVEHOME,WhereExpensiveHomes
import folium
from folium.plugins import HeatMap
main = Blueprint('main', __name__)


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
    m = WhereExpensiveHomes(minprice,days)
    return render_template('WhereToBuild.html', m=m, minprice=minprice, days=days)

@main.route('/showdb')
def showtable():
    # Use a subset of your listings or dummy data for testing
    UpdateListfromLocation('Bellevue', Listing, db)

    listings = Listing.query.all()
    return render_template('table_template.html', listings=listings)

@main.route('/newlistings')
def newlistings():
    # Use a subset of your listings or dummy data for testing
    SearchNewListing('Bellevue', Listing, db)
    SearchNewListing('Kenmore', Listing, db)
    SearchNewListing('Bothell', Listing, db)
    SearchNewListing('Kirkland', Listing, db)
    # UpdateListfromLocation('Bellevue', Listing, db)

    listings = Listing.query.filter(Listing.daysOnZillow > -1).order_by(Listing.daysOnZillow).all()
    return render_template('table_template.html', listings=listings)

AreasToCareAbout =['Bellevue', 'Kenmore', 'Bothell' ,'Kirkland' ,'Seattle', 'Shoreline' ,'Renton', 'Kent' ,'Mercer' ,'Island']
@main.route('/allthesoldhomes')
def AllSoldHomes():
    # Use a subset of your listings or dummy data for testing
    # SearchNewSoldHomes('Bellevue')
    # SearchNewSoldHomes('Kenmore')
    # SearchNewSoldHomes('Bothell')
    # SearchNewSoldHomes('Kirkland')
    # SearchNewSoldHomes('Ballard')
    # SearchNewSoldHomes('Fremont')
    # SearchNewSoldHomes('Phinney Ridge')
    # SearchNewSoldHomes('Wallingford')
    #
    # SearchNewSoldHomes('Shoreline')
    # SearchNewSoldHomes('Renton', "12m")
    # SearchNewSoldHomes('Clyde Hill', "12m")
    SearchNewSoldHomes('Medina', "12m")
    # SearchNewSoldHomes('Mercer Island', "12m")
    # SearchNewSoldHomes('Seattle', "12m")
    # UpdateListfromLocation('Bellevue', Listing, db)

    listings = Listing.query.order_by(Listing.dateSold).all()
    return render_template('table_template.html', listings=listings)


@main.route('/beaman', methods=['GET', 'POST'])
def searchdb():
    listings = Listing.query.all()
    for soldhouse in listings:
        listinglengthdays = ListingLength(soldhouse, Listing, db)
    return render_template('table_template.html', listings=listings)


@main.route('/downloadpicsfromMLS', methods=['GET','POST'])
def download_pics():
    if request.method == 'POST':
        ref_number = request.form.get('ref_number')
        success = PicturesFromMLS(ref_number, Listing, db)
        if success:  # Check if API was called successfully
            return jsonify(status="success", message="API called successfully")
        else:
            return jsonify(status="error", message="API call failed")
    return render_template('MLS_Input.html')


@main.route('/givemecomps', methods=['GET','POST'])
def GiveMeComps():
    if request.method == 'POST':
        ref_number = request.form.get('ref_number')
        success = PicturesFromMLS(ref_number, Listing, db)
        if success:  # Check if API was called successfully
            return jsonify(status="success", message="API called successfully")
        else:
            return jsonify(status="error", message="API call failed")
    return render_template('MLS_Input.html')

def call_api_with_ref(ref_number):
    # Logic to call the API with the reference number
    # This is a placeholder, replace with actual API call
    return True  # return True if successful, else False

# @main.route('/upload', methods=['GET', 'POST'])
# def upload_csv():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file:
#             filename = secure_filename(file.filename)
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(filepath)
#             import_csv_to_db(filepath)
#             flash('CSV imported successfully!')
#             return redirect(url_for('index'))
#
#     return render_template_string("""
#         <h1>Upload CSV</h1>
#         <form method="post" enctype="multipart/form-data">
#             <input type="file" name="file">
#             <input type="submit" value="Upload">
#         </form>
#     """)