import requests
# base = "http://127.0.0.1:5000/"
base = "https://www.drillbreaker29.com/"

getcitylisturl = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"
getsoldlistingsurl = base + "maintanance/maintainSoldListings"
getforsalelistingsurl = base + "maintanance/maintainFORSALEListings"
getpendinglistingsurl = base + "maintanance/maintainPendingListings"
# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"{base}maintanance/fsbo"
urlopen = f"{base}maintanance/updateopenhouse"

params = []
payload = {}
headers = {}

response = requests.request("GET", getcitylisturl,  params=params, headers=headers, data=payload)


for i,city in enumerate(response.json()["cities"]):
    print(city)

    payload = {'doz': '60',
               'city': city}
    files = []
    headers = {}

    res = requests.request("PATCH", getsoldlistingsurl, headers=headers, data=payload, files=files)
    print(res)
    payload = {'doz': '180',
               'city': city}
    res = requests.request("PATCH", getforsalelistingsurl, headers=headers, data=payload, files=files)
    # resp = requests.request("PATCH", url3, headers=headers, data=payload)
    print(res)
    payload = {'doz': '60',
               'city': city}
    res = requests.request("PATCH", getpendinglistingsurl, headers=headers, data=payload, files=files)
    # resp = requests.request("PATCH", url3, headers=headers, data=payload)
    print(res)

payload = {}
response = requests.request("POST", base+"zonestats/update", headers=headers, data=payload)



url_health = f"{base}email/email_healthcheck"
payload = {'message': "completed listing maintenance"}
response = requests.request("GET", url_health, headers=headers, data=payload)

