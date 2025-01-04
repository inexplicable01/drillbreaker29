import requests
base = "http://127.0.0.1:5000/"
# base = "https://www.drillbreaker29.com/"

url = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

for i,city in enumerate(response.json()["cities"]):
    print(city)
    # if i<185:
    #     continue
    url = base + "maintanance/maintainListings"

    payload = {'doz': '365',
               'city': city}
    files = [

    ]
    headers = {}

    response = requests.request("PATCH", url, headers=headers, data=payload, files=files)

    response = requests.request("PATCH", url3, headers=headers, data=payload)

