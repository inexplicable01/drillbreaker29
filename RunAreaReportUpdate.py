import requests
import os

url = f"{os.getenv('ENDPOINT')}/areareport"

payload = {}
headers = {}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)
