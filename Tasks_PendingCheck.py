import requests

url = "https://www.drillbreaker29.com/email/email_pendingcheck"

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
