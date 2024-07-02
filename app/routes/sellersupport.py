# email_bp.py
from flask import Blueprint, redirect, url_for,request
from datetime import datetime, timedelta
from app.ZillowAPI.ZillowAPICall import SearchZillowByAddress

sellersupport_bp = Blueprint('sellersupport_bp', __name__, url_prefix='/sellersupport')


@sellersupport_bp.route('/sellerhomedetails', methods=['GET'])
def neighcleanup():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    # cleanupresults = brieflistingcontroller.listingsN_Cleanup()

    fulladdress = request.form.getlist('fulladdress')

    try:
        propertydata = SearchZillowByAddress(fulladdress)
        bedrooms = propertydata["bedrooms"]
        bathrooms = propertydata["bathrooms"]
        livingArea = propertydata["livingArea"]
        zestimate = propertydata["zestimate"]
        imgSrc = propertydata["desktopWebHdpImageLink"]

    except Exception as e:
        bedrooms = 999
        bathrooms = 999
        livingArea = 9
        zestimate = 9
        imgSrc = ''

    return {'bedrooms': bedrooms, 'bathrooms': bathrooms, 'livingArea': livingArea ,'zestimate':zestimate, 'imgSrc':imgSrc}, 200



@sellersupport_bp.route('/schedule', methods=['GET'])
def schedule():
    # Assuming sendEmailwithNewListing() is a function that sends an email with new listings.
    # cleanupresults = brieflistingcontroller.listingsN_Cleanup()

    cleaner = request.form.get('cleaner')
    stager = request.form.get('stager')
    photographer = request.form.get('photographer')
    titlecompany = request.form.get('titlecompany')
    legaladvisor = request.form.get('legaladvisor')
    mover = request.form.get('mover')
    zipcode = request.form.get('zipcode')
    desiredclosingdate= request.form.get('desiredclosingdate')

    closing_date = datetime.strptime(desiredclosingdate, "%m-%d-%Y")

    start_date = closing_date - timedelta(weeks=6)

    # Define the task durations and sequences
    tasks = [
        {"service": "Cleaning","serviceVendor":cleaner, "duration": 3, "cost":500},
        {"service": "Staging", "serviceVendor":stager, "duration": 3, "cost":5000},
        {"service": "Photography", "serviceVendor":photographer, "duration": 1 , "cost":600},
        {"service": "Listing", "serviceVendor":'Agent', "duration": 14 ,"cost":0},
        {"service": "Open House", "serviceVendor":'Agent', "duration": 1,"cost":0},
        {"service": "Final Walkthrough", "serviceVendor":'Agent', "duration": 1, "cost":0},
        {"service": "Closing", "serviceVendor":titlecompany, "duration": 17,  "cost":3000},
        # {"service": "Title and Escrow", "serviceVendor":titlecompany, "duration": 9},
        {"service": "Legal Review","serviceVendor":legaladvisor,  "duration": 1,"cost":2000},
        {"service": "Moving", "serviceVendor":mover, "duration": 2,"cost":5000}
    ]

    current_date = start_date

    # Schedule each task and update the current date
    schedule = []
    for task in tasks:
        task_start_date = current_date
        task_end_date = current_date + timedelta(days=task["duration"] - 1)
        schedule.append({
            "service": task["service"],
            "start_date": task_start_date.strftime("%B %d"),
            "end_date": task_end_date.strftime("%B %d"),
            # "status": "Pending",
            "serviceVendor": task["serviceVendor"],
            "cost": task["cost"]  # Assuming cost will be handled separately
        })
        # Move the current date to the day after the task ends
        current_date = task_end_date + timedelta(days=1)

    return {"schedule":schedule , "taxes":50000}, 200


# Example usage
# desired_closing_date = "07-16-2024"  # Example closing date in MM-DD-YYYY format
# task_schedule = schedule_tasks(desired_closing_date)

# Display the scheduled tasks
# for task in task_schedule:
#     print(
#         f"Service: {task['service']}, Start Date: {task['start_date']}, End Date: {task['end_date']}, Status: {task['status']}, Cost: {task['cost']}")
    # please write code here that will populate the list in the picture,  based on the desiredclosingdate, note that the desiredclosingdatewill be supplied in this format MM-DD-YYYY
    # Use your logic to plan out the various tasks that needs to get done to get to property listing.   Assume a 6 week time between listing and desiredclosingdate

    # return listofdates, 200