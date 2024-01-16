import os

import requests

url = f"{os.getenv('ENDPOINT')}/sendEmailUpdates"

payload = {}
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)