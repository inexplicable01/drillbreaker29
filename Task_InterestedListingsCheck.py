import requests
# base = "http://127.0.0.1:5000/"
base = "https://www.drillbreaker29.com/"


url = f"{base}maintanance/checkInterestedListingsChange"

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
