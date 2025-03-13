import requests
base = "http://127.0.0.1:5000/"
# base = "https://www.drillbreaker29.com/"


url = f"{base}listingalerts/activeCustomers"

payload = {}
headers = {}
# print(url)
response = requests.request("GET", url, headers=headers, data=payload)

activeCustomers = response.json()['activeCustomers']
# print(activeCustomers)

# for customer in activeCustomers:
#     print(customer)
#     url = f"{base}maintanance/clients_listing_Recommendation?customer_id={customer['id']}"
#
#     response = requests.request("PATCH", url, headers=headers, data=payload)

for customer in activeCustomers:
    print(customer)
    url = f"{base}customer_interest/send_email/{customer['id']}"

    response = requests.request("POST", url, headers=headers, data=payload)
