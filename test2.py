
import requests


def get_bounding_coordinates(place_name, api_key):
    # Step 2: Geocode the place name
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={api_key}"
    geocode_response = requests.get(geocode_url).json()
    location = geocode_response['results'][0]['geometry']['location']


    print(location)

    # # Step 3: Get Place ID
    # places_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=place_id&key={api_key}"
    # places_response = requests.get(places_url).json()
    # place_id = places_response['candidates'][0]['place_id']
    #
    # # Step 4: Get Place Details
    # details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
    # details_response = requests.get(details_url).json()
    # viewport = details_response['result']['geometry']['viewport']
    #
    # northeast = viewport['northeast']
    # southwest = viewport['southwest']

    # return northeast, southwest


# Example usage
api_key = "AIzaSyCRari3R_CTTF8NbXmXCsvde8UXGCeT0Aw"
place_name = "Norkirk, Kirkland, WA"
northeast, southwest = get_bounding_coordinates(place_name, api_key)
print(f"Northeast: {northeast}")
print(f"Southwest: {southwest}")