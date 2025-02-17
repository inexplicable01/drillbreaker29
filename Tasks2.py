import requests
# base = "http://127.0.0.1:5000/"
base = "https://www.drillbreaker29.com/"

getcitylisturl = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"
getlistingsurl = base + "maintanance/maintainListings"
# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"{base}maintanance/fsbo"
urlopen = f"{base}maintanance/updateopenhouse"

payload = {}
headers = {}

response = requests.request("GET", getcitylisturl, headers=headers, data=payload)

for i,city in enumerate(response.json()["cities"]):
    print(city)

    payload = {'doz': '365',
               'city': city}
    files = []
    headers = {}

    res = requests.request("PATCH", getlistingsurl, headers=headers, data=payload, files=files)
    resp = requests.request("PATCH", url3, headers=headers, data=payload)

payload = {}
response = requests.request("POST", base+"zonestats/update", headers=headers, data=payload)



url_health = f"{base}email/email_healthcheck"
payload = {'message': "completed listing maintenance"}
response = requests.request("GET", url_health, headers=headers, data=payload)

