import requests
base = "http://127.0.0.1:5000/"
# base = "https://www.drillbreaker29.com/"


url = f"{base}listingalerts/activeCustomers"

payload = {}
headers = {}
# print(url)
response = requests.request("GET", url, headers=headers, data=payload)

activeCustomers = response.json()['activeCustomers']

for customer in activeCustomers:
    print(customer)
    # url = f"{base}customer_interest/send_email/{customer['id']}"
    #
    # response = requests.request("POST", url, headers=headers, data=payload)
