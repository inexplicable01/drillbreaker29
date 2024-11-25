import requests
import os


# url2 = f"https://www.drillbreaker29.com/maintanance/updatelistings"
url3 = f"https://www.drillbreaker29.com/maintanance/listingscheck"
urlfsbo = f"https://www.drillbreaker29.com/maintanance/fsbo"
urlopen = f"https://www.drillbreaker29.com/maintanance/updateopenhouse"

##Need FSBO weekly Update
##Need All ForSale Listing Weekly Update

payload = {}
headers = {}

# response = requests.request("PATCH", url2, headers=headers, data={'doz': '1095'})
response = requests.request("PATCH", url3, headers=headers, data=payload)
response = requests.request("PATCH", urlfsbo, headers=headers, data=payload)
response = requests.request("PATCH", urlopen, headers=headers, data=payload)

print(response.text)
