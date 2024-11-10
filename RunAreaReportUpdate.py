import requests
import os

url = f"https://www.drillbreaker29.com/soldhomes/areareport"
url2 = f"https://www.drillbreaker29.com/maintanance/updatelistings"
payload = {}
headers = {}

response = requests.request("POST", url2, headers=headers, data={'doz': '1095'})
response = requests.request("PATCH", url, headers=headers, data=payload)
print(response.text)
