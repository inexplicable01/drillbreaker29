import requests

url = "https://www.drillbreaker29.com/maintanance/updateathing3?iter=250"

payload = {}
headers = {}
import time

for i in range(0,10000):
    response = requests.request("POST", url, headers=headers, data=payload)
    time.sleep(1)

print(response.text)
