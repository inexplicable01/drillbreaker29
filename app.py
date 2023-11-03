



# def check_new_listings():
#     # Placeholder for your API check
#     # api_url = "YOUR_REAL_ESTATE_API_URL"
#     # response = requests.get(api_url)
#     # data = response.json()
#     # new_listings = []
#
#     # for listing in data:
#     #     if not Listing.query.filter_by(api_id=listing['id']).first():
#     #         new_listing = Listing(api_id=listing['id'])
#     #         db.session.add(new_listing)
#     #         new_listings.append(listing)
#     #
#     # db.session.commit()
#     #
#     # if new_listings:
#     test_listings = [{'id': 1,
#             'details':'asdfasdf'},
#             {'id': 2,
#             'details':'tyjkhggg'}]
#
#     email_content = "Scheduled New Listings:\n"
#     for listing in test_listings:
#         email_content += f"ID: {listing['id']}, Details: {listing['details']}\n"
#     send_email('New Listing', email_content)


#
#
# # if __name__ == '__main__':
# app = create_app()
# # scheduler = BackgroundScheduler()
# # scheduler.add_job(func=check_new_listings, trigger="interval", minutes=1)
# # scheduler.start()
#     # app.run()
from app import create_app, db
import logging

file_handler = logging.FileHandler('flask_errors.log')
file_handler.setLevel(logging.ERROR)

app = create_app(debug=True)
app.logger.addHandler(file_handler)
if __name__ == '__main__':
    app.run()