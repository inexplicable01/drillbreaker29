import requests
base = "http://127.0.0.1:5000/"
base = "https://www.drillbreaker29.com/"

url = base + "maintanance/getCityList"
url3 = base + "maintanance/listingscheck"

# url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"https://www.drillbreaker29.com/maintanance/fsbo"
urlopen = f"https://www.drillbreaker29.com/maintanance/updateopenhouse"

payload = {}
headers = {}


response = requests.request("PATCH", urlfsbo, headers=headers, data=payload)
response = requests.request("PATCH", urlopen, headers=headers, data=payload)
url = "https://www.drillbreaker29.com/email/email_healthcheck"
payload = {'message': "completed FSBO listing maintenance"}
response = requests.request("GET", url, headers=headers, data=payload)

