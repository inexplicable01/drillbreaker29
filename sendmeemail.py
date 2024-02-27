import requests

# The URL you want to make a POST request to
url = "https://www.drillbreaker29.com/sendEmailUpdates"

# Any data you want to send in the POST request
# This is optional and depends on what your endpoint expects
data = {
    "key": "value"  # Example data - replace with actual data if needed
}

# Optional: Headers you might need to send (like Content-Type, Authorization, etc.)
headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer YOUR_TOKEN_HERE",  # Uncomment and replace if needed
}

# Making the POST request
response = requests.post(url, json=data, headers=headers)

# Checking if the request was successful
if response.status_code == 200:
    print("Successfully made the POST request.")
    # Optionally, print the response content
    print(response.text)
else:
    print("Failed to make the POST request.")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
