import requests
import os

url = f"https://www.drillbreaker29.com/soldhomes/areareport"

payload = {}
headers = {}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)
