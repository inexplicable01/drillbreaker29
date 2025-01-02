import requests

url = "http://127.0.0.1:5000/maintanance/getCityList"

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

for city in response.json()["cities"]:
    print(city)
    url = "http://127.0.0.1:5000/maintanance/maintainListings"

    payload = {'doz': '30',
               'city': city}
    files = [

    ]
    headers = {}

    response = requests.request("PATCH", url, headers=headers, data=payload, files=files)

