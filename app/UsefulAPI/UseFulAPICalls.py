import requests
import os
api_key = os.getenv('GOOGLE_API_KEY')

def get_neighborhood(lat, lon):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    try:
        for component in data['results'][0]['address_components']:
            if 'neighborhood' in component['types']:
                return component['long_name']
        for component in data['results'][0]['address_components']:
            if 'locality' in component['types']:
                return component['long_name']
        return None
    except:
        return None