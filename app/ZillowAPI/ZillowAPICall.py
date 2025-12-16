import requests
import os
from warnings import warn
import time

import sqlite3
from dotenv import load_dotenv

# Load API key
load_dotenv()

# Global headers for new zllw-working-api
headers = {
    "x-rapidapi-key": os.getenv('RAPID_API_KEY'),
    "x-rapidapi-host": "zllw-working-api.p.rapidapi.com"
}

# Legacy field keys (kept for reference)
keystokeep = ['zpid','price','unit','streetAddress',
              'city','state','zipcode','bedrooms',
              'bathrooms','zestimate','daysOnZillow',
              'dateSold','homeType','latitude','longitude']

def normalize_home_status(new_status):
    """
    Normalize homeStatus from new API format to old API format.
    This ensures backward compatibility with existing database and code.

    Maps all API variations to the old format your codebase expects:
    - 'Sold', 'Recently_Sold', 'SOLD', 'recentlySold' → 'RECENTLY_SOLD'
    - 'For_Sale', 'forSale' → 'FOR_SALE'
    - 'Pending' → 'PENDING'
    - 'Off_Market', 'Other' → 'OTHER'
    """
    if not new_status:
        return new_status

    status_mapping = {
        # New API formats (with underscores) - these are what the new API returns
        'Sold': 'RECENTLY_SOLD',
        'Recently_Sold': 'RECENTLY_SOLD',
        'For_Sale': 'FOR_SALE',
        'Pending': 'PENDING',
        'Off_Market': 'OTHER',
        'Other': 'OTHER',
        # Legacy formats found in old data (camelCase and uppercase variants)
        'SOLD': 'RECENTLY_SOLD',
        'forSale': 'FOR_SALE',
        'recentlySold': 'RECENTLY_SOLD'
    }
    return status_mapping.get(new_status, new_status)

def normalize_home_type(new_type):
    """
    Normalize homeType from new API format to old API format.
    This ensures backward compatibility with existing database and code.

    Maps all API variations to the old format your codebase expects:
    - 'singleFamily' → 'SINGLE_FAMILY'
    - 'townhome' → 'TOWNHOUSE'
    - 'condo' → 'CONDO'
    - 'apartment' → 'APARTMENT'
    - 'multiFamily' → 'MULTI_FAMILY'
    - 'land' → 'LOT'
    - 'manufactured' → 'MANUFACTURED'
    """
    if not new_type:
        return new_type

    type_mapping = {
        # New API formats (camelCase) - these are what the new API returns
        'singleFamily': 'SINGLE_FAMILY',
        'townhome': 'TOWNHOUSE',
        'condo': 'CONDO',
        'apartment': 'APARTMENT',
        'multiFamily': 'MULTI_FAMILY',
        'land': 'LOT',
        'manufactured': 'MANUFACTURED',
        # Handle any legacy uppercase variants that might exist
        'SINGLE_FAMILY': 'SINGLE_FAMILY',
        'TOWNHOUSE': 'TOWNHOUSE',
        'CONDO': 'CONDO',
        'APARTMENT': 'APARTMENT',
        'MULTI_FAMILY': 'MULTI_FAMILY',
        'LOT': 'LOT',
        'MANUFACTURED': 'MANUFACTURED'
    }
    return type_mapping.get(new_type, new_type)

def normalize_brief_listing(search_result):
    """
    Normalize a brief listing from the new API format to match old API format.
    Extracts the 'property' wrapper and flattens nested fields for backward compatibility.
    """
    if not search_result or 'property' not in search_result:
        return search_result

    prop = search_result['property']
    normalized = prop.copy()

    # Flatten location fields
    if 'location' in prop and isinstance(prop['location'], dict):
        normalized['latitude'] = prop['location'].get('latitude')
        normalized['longitude'] = prop['location'].get('longitude')

    # Flatten address fields to top level
    if 'address' in prop and isinstance(prop['address'], dict):
        address = prop['address']
        normalized['streetAddress'] = address.get('streetAddress')
        normalized['city'] = address.get('city')
        normalized['state'] = address.get('state')
        normalized['zipcode'] = address.get('zipcode')

    # Flatten price
    if 'price' in prop and isinstance(prop['price'], dict):
        normalized['price'] = prop['price'].get('value')
        normalized['pricePerSquareFoot'] = prop['price'].get('pricePerSquareFoot')

    # Map image source
    if 'media' in prop and isinstance(prop['media'], dict):
        if 'propertyPhotoLinks' in prop['media']:
            photo_links = prop['media']['propertyPhotoLinks']
            normalized['imgSrc'] = photo_links.get('highResolutionLink') or photo_links.get('mediumSizeLink')

    # Map property type and normalize to old API format
    if 'propertyType' in prop:
        normalized['homeType'] = normalize_home_type(prop['propertyType'])

    # Map listing status and normalize to old API format
    if 'listing' in prop and isinstance(prop['listing'], dict):
        new_status = prop['listing'].get('listingStatus')
        normalized['homeStatus'] = normalize_home_status(new_status)

    # Map estimates
    if 'estimates' in prop and isinstance(prop['estimates'], dict):
        normalized['zestimate'] = prop['estimates'].get('zestimate')

    # Map tax assessment
    if 'taxAssessment' in prop and isinstance(prop['taxAssessment'], dict):
        normalized['taxAssessedValue'] = prop['taxAssessment'].get('taxAssessedValue')

    # Map lot size
    if 'lotSizeWithUnit' in prop and isinstance(prop['lotSizeWithUnit'], dict):
        normalized['lotAreaValue'] = prop['lotSizeWithUnit'].get('lotSize')
        normalized['lotAreaUnit'] = prop['lotSizeWithUnit'].get('lotSizeUnit')

    # Keep other fields as-is (zpid, bathrooms, bedrooms, livingArea, daysOnZillow, etc.)

    return normalized

def SearchZillowByZPID(ZPID):
    querystring = {"zpid": ZPID}
    url = "https://zllw-working-api.p.rapidapi.com/pro/byzpid"
    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)
    try:
        data = response.json()
        # Extract propertyDetails to maintain backward compatibility
        property_details = data.get('propertyDetails', data)

        # Flatten nested address fields for backward compatibility
        if property_details and 'address' in property_details and isinstance(property_details['address'], dict):
            address = property_details['address']
            # Copy nested address fields to top level if they don't already exist
            if 'streetAddress' not in property_details:
                property_details['streetAddress'] = address.get('streetAddress')
            if 'zipcode' not in property_details:
                property_details['zipcode'] = address.get('zipcode')
            # Note: city and state already exist at top level in new API

        # Map image field names for backward compatibility
        if property_details:
            if 'imgSrc' not in property_details and 'hiResImageLink' in property_details:
                property_details['imgSrc'] = property_details['hiResImageLink']
            # Also provide desktopWebHdpImageLink as fallback
            if 'desktopWebHdpImageLink' not in property_details and 'hiResImageLink' in property_details:
                property_details['desktopWebHdpImageLink'] = property_details['hiResImageLink']

            # Normalize homeStatus to old API format for backward compatibility
            if 'homeStatus' in property_details:
                property_details['homeStatus'] = normalize_home_status(property_details['homeStatus'])

            # Normalize homeType to old API format for backward compatibility
            if 'homeType' in property_details:
                property_details['homeType'] = normalize_home_type(property_details['homeType'])

        return property_details
    except Exception as e:
        warn(f"Search Zillow zpid {ZPID} failed due to an exception: {e}")
        return None

def SearchZilowByMLSID(MLSID):
    """
    Search for a property by MLS ID and return the zpid and property data (if fetched).

    Returns:
        tuple: (zpid, propertydata) where:
            - zpid (str): The Zillow property ID for the WA property, or None if not found
            - propertydata (dict): Full property details if we had to fetch them (for blank addresses),
                                   or None if we found a WA property using address (no fetch needed)

    Note: If propertydata is not None, caller can skip calling SearchZillowByZPID again.
    """
    querystring = {"mlsid": MLSID}
    url = "https://zllw-working-api.p.rapidapi.com/search/bymls"
    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)

    try:
        data = response.json()

        # New API returns 'searchResult' (singular), not 'data' array
        if 'searchResult' not in data:
            warn(f"No searchResult found for MLSID {MLSID}. Response: {data}")
            return None, None

        search_result = data['searchResult']

        # Defensive check: warn if searchResult is unexpectedly a list
        if isinstance(search_result, list):
            warn(f"WARNING: searchResult is a list (expected dict) for MLSID {MLSID}. Taking first result.")
            if len(search_result) == 0:
                warn(f"Empty searchResult list for MLSID {MLSID}.")
                return None, None
            search_result = search_result[0]  # Take first result

        # Extract zpid directly from searchResult
        zpid = search_result.get('zpid')

        if not zpid:
            warn(f"No zpid found in searchResult for MLSID {MLSID}.")
            return None, None

        # Check if the property is in WA (new API has structured address)
        if 'address' in search_result and isinstance(search_result['address'], dict):
            if search_result['address'].get('state') == 'WA':
                # Return zpid only, no propertydata fetched (fast path)
                return zpid, None

        # If we can't verify state from address, fetch full property details
        property_details = SearchZillowByZPID(zpid)

        # Check if the property is in WA
        if property_details and 'address' in property_details:
            address_info = property_details['address']
            if address_info.get('state') == 'WA':
                # Return both zpid AND property_details we just fetched
                return zpid, property_details

        warn(f"No property in WA found for MLSID {MLSID}.")
        return None, None

    except Exception as e:
        warn(f"Search Zillow MLS ID {MLSID} failed due to an exception: {e}")
        return None, None

def SearchZillowByAddress(addressStr):
    """
    Search by address, then fetch full details via ZPID.
    This centralizes all backward compatibility logic in SearchZillowByZPID.
    """
    querystring = {"propertyaddress": addressStr}
    url = "https://zllw-working-api.p.rapidapi.com/pro/byaddress"
    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)

    if response.status_code == 502:
        warn('502 on ' + addressStr)
        return None

    try:
        data = response.json()

        # Extract zpid from response
        property_details = data.get('propertyDetails', data)
        zpid = property_details.get('zpid')

        if not zpid:
            warn(f"No zpid found for address: {addressStr}")
            return None

        # Get full property details via SearchZillowByZPID (which has all backward compatibility logic)
        return SearchZillowByZPID(zpid)

    except Exception as e:
        warn(f"Search Zillow failed due to an exception: {e}")
        return None

def SearchZillowBriefListingByAddress(addressStr):
    """
    Get brief listing by full address.
    Updated to use new zllw-working-api and normalize results.
    """
    url = "https://zllw-working-api.p.rapidapi.com/search/byaddress"
    querystring = {
        "location": addressStr,
        "listingStatus": "For_Sale",
        "daysOnZillow": "Any",
        "page": "1"
    }

    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)

    if response.status_code == 502:
        warn('502 on ' + addressStr)
        return None

    try:
        result = response.json()
        search_results = result.get('searchResults', [])

        if len(search_results) > 0:
            # Return first result, normalized
            return normalize_brief_listing(search_results[0])
        else:
            warn(f"No results found for address: {addressStr}")
            return None

    except Exception as e:
        warn(f"Search Zillow failed due to an exception: {e}")
        return None

#
# def RentEstimateBriefListing(addressStr):
#     """
#     Get rent estimate for an address.
#     Updated to use new zllw-working-api.
#     """
#     url = "https://zllw-working-api.p.rapidapi.com/rent/estimate"
#     querystring = {"address": addressStr}
#
#     response = requests.get(url, headers=headers, params=querystring)
#     time.sleep(0.5)
#
#     if response.status_code == 502:
#         warn('502 on ' + addressStr)
#         return None
#
#     try:
#         return response.json()
#     except Exception as e:
#         warn(f"Rent estimate failed due to an exception: {e}")
#         return None


# def SearchZillowNewListingByLocation(location, daysonzillow):
#     """
#     Simple location search without sqft filtering.
#     Updated to use new zllw-working-api and normalize results.
#     """
#     url = "https://zllw-working-api.p.rapidapi.com/search/byaddress"
#     curpage = 1
#     maxpage = 2
#     houseresult = []
#
#     while maxpage >= curpage:
#         querystring = {
#             "location": location + ", WA",
#             "page": str(curpage),
#             "listingStatus": "For_Sale",
#             "daysOnZillow": str(daysonzillow),
#             "sortOrder": "Homes_for_you"
#         }
#
#         response = requests.get(url, headers=headers, params=querystring)
#         time.sleep(0.5)
#
#         if response.status_code == 502:
#             warn('502 on ' + location)
#             return houseresult
#
#         try:
#             result = response.json()
#
#             # Get and normalize search results
#             search_results = result.get('searchResults', [])
#             for search_result in search_results:
#                 normalized = normalize_brief_listing(search_result)
#                 houseresult.append(normalized)
#
#             curpage = curpage + 1
#             print(curpage)
#
#             # Get pagination from new API structure
#             if 'pagesInfo' in result:
#                 maxpage = result['pagesInfo'].get('totalPages', 0)
#
#         except Exception as e:
#             warn(e.__str__())
#             return houseresult
#
#     return houseresult

# def SearchZillowNewListingByInterest(location, beds_min, beds_max, baths_min, price_max, daysonzillow):
#     """
#     Location search with bed/bath/price filters.
#     Updated to use new zllw-working-api and normalize results.
#     """
#     url = "https://zllw-working-api.p.rapidapi.com/search/byaddress"
#     curpage = 1
#     maxpage = 2
#     houseresult = []
#
#     while maxpage >= curpage:
#         querystring = {
#             "location": location + ", WA",
#             "page": str(curpage),
#             "listingStatus": "For_Sale",
#             "price_max": str(price_max),
#             "bed_min": str(beds_min),
#             "bed_max": str(beds_max),
#             "bath_min": str(baths_min),
#             "sortOrder": "Homes_for_you"
#         }
#
#         response = requests.get(url, headers=headers, params=querystring)
#         time.sleep(0.5)
#
#         if response.status_code == 502:
#             warn('502 on ' + location)
#             return houseresult
#
#         try:
#             result = response.json()
#
#             # Get and normalize search results
#             search_results = result.get('searchResults', [])
#             for search_result in search_results:
#                 normalized = normalize_brief_listing(search_result)
#                 houseresult.append(normalized)
#
#             print(location, curpage)
#             curpage = curpage + 1
#
#             # Get pagination from new API structure
#             if 'pagesInfo' in result:
#                 maxpage = result['pagesInfo'].get('totalPages', 0)
#
#         except Exception as e:
#             warn(e.__str__())
#             return houseresult
#
#     return houseresult

zillowapi_intervals= ['Any','1_day','7_days','30_days','90_days','6_months','12_months','24_months','36_months'];

def SearchZillowHomesByLocation(location, status="Sold", soldInLast = "90_days", max_sqft = 10000):
    """
    Search homes by location with sqft range filtering (your original proven logic).
    Updated to use new zllw-working-api and normalize results.
    """
    url = "https://zllw-working-api.p.rapidapi.com/search/byaddress"

    houseresult = []
    print(f'Searching {status} homes in location: {location}')

    interval = 1000
    minhomesize = 0
    maxhomesize = interval + minhomesize

    seen_ids = set()

    min_interval = 20

    while True:
        lastpage = 1
        maxpage = 2
        maxpagebackup = 2
        results_in_this_interval = []
        should_restart = False  # Flag to control outer loop

        while maxpage >= lastpage:
            # Full querystring with all standard parameters
            querystring = {
                "location": f"{location}, WA",
                "page": str(lastpage),
                "sortOrder": "Homes_for_you",
                "listingStatus": status,
                "bed_min": "No_Min",
                "bed_max": "No_Max",
                "bathrooms": "Any",
                "homeType": "Houses, Townhomes, Multi-family, Condos/Co-ops, Lots-Land, Apartments, Manufactured",
                "maxHOA": "Any",
                "listingType": "By_Agent",
                "listingTypeOptions": "Agent listed,New Construction,Fore-closures,Auctions",
                "parkingSpots": "Any",
                "mustHaveBasement": "No",
                "daysOnZillow": "Any",
                "soldInLast": soldInLast,
                "squareFeetRange": f"min:{str(minhomesize)}, max: {str(maxhomesize)}",
            }

            print(f"Search {minhomesize}–{maxhomesize} sqft, page {lastpage}, status={status}")
            response = requests.get(url, headers=headers, params=querystring)
            time.sleep(1.0)

            if response.status_code == 502:
                warn(f'502 error on {location}')
                should_restart = True
                break

            try:
                result = response.json()

                # Get pagination from new API structure
                total_results = result.get('resultsCount',0)
                totalMatchingCount = total_results.get('totalMatchingCount',0)
                print(f'{totalMatchingCount} for {minhomesize}–{maxhomesize} size.')
                if 'pagesInfo' in result:
                    maxpage = result['pagesInfo'].get('totalPages', 0)
                    if maxpage != 0:
                        maxpagebackup = maxpage

                # Get and normalize search results
                search_results = result.get('searchResults', [])
                for search_result in search_results:
                    normalized = normalize_brief_listing(search_result)
                    results_in_this_interval.append(normalized)

                print(f'Page {lastpage} of {maxpage} processed.')
                lastpage += 1

                if maxpage == 0:
                    maxpage = maxpagebackup
                    print('No results found.')

                if totalMatchingCount >= 1000:
                    print("Search too large for interval, reducing...")
                    interval = max(min_interval, interval // 2)
                    maxhomesize = minhomesize + interval
                    should_restart = True
                    break  # break inner, continue outer
            except Exception as e:
                print("Search Zillow failed due to an exception:", e)
                break

        if should_restart:
            continue  # restart outer loop with adjusted interval

        if maxhomesize >= max_sqft:
            print("All intervals processed.")
            break

        for listing in results_in_this_interval:
            zpid = listing.get('zpid')
            if zpid and zpid not in seen_ids:
                seen_ids.add(zpid)
                houseresult.append(listing)
        print(f'Found {len(houseresult)} unique results Cummulatively.')

        # Move to the next range with small overlap
        minhomesize = maxhomesize
        maxhomesize = min(minhomesize + interval, max_sqft)

    return houseresult


# def SearchZillowHomesByLocationbackup(location, status="recentlySold", doz=14, timeOnZillow=14):
#     houseresult = []
#     print(f'Searching {status} homes in location: {location}')
#
#     interval = 10000
#     minhomesize = 0
#     maxhomesize = interval + minhomesize
#
#     while True:
#         lastpage = 1
#         maxpage = 2
#         results_in_this_interval = []
#
#         while maxpage >= lastpage:
#             querystring = {
#                 "location": f"{location}, WA",
#                 "page": str(lastpage),
#                 "status": status,
#                 "output": "json",
#                 # "sortSelection": "priorityscore",
#                 "listing_type": "by_agent",
#                 "sqft_min": str(minhomesize),
#                 "sqft_max": str(maxhomesize),
#                 "doz": doz if status == "recentlySold" else doz,
#                 "timeOnZillow": timeOnZillow if status == "forSale" else None,
#                 "isMultiFamily": "false",
#             }
#             querystring = {k: v for k, v in querystring.items() if v is not None}
#
#             print(f"Search {minhomesize} to {maxhomesize} with status{status}.")
#             response = requests.get(url, headers=headers, params=querystring)
#             time.sleep(0.5)
#
#             if response.status_code == 502:
#                 warn(f'502 error on {location}')
#                 break
#
#             try:
#                 result = response.json()
#
#
#                 if result.get('totalPages') >= 20:
#                     print("Search too large, reducing interval.")
#                     interval //= 2
#                     maxhomesize = minhomesize + interval  # Adjust the range
#                     continue  # Restart the outer loop with updated interval
#                 maxpage = result.get('totalPages')
#                 results_in_this_interval.extend(result.get('results', []))
#                 print(f'Page {lastpage} of {maxpage} processed.')
#                 lastpage += 1
#
#             except Exception as e:
#                 print("Search Zillow failed due to an exception:", e)
#                 break
#
#         houseresult.extend(results_in_this_interval)
#
#         # Check if interval is small enough or search is complete
#         if maxpage < 20:
#             if interval == 1:
#                 print("Search complete with current interval.")
#                 break
#
#         if maxpage < 3:
#             interval = 2*interval
#
#
#
#         # Move to the next range
#         if maxpage <= 20 and minhomesize + interval >= 10000:  # Arbitrary max size for demonstration
#             print("All intervals processed.")
#             break
#
#         minhomesize = maxhomesize
#         maxhomesize = minhomesize + interval
#
#     print(f'Found {len(houseresult)} results.')
#     return houseresult
#
def SearchZillowHomesByZone(zone, status="Sold", soldInLast="90_days"):
    """
    Search homes by polygon zone with sqft range filtering.
    Updated to use new zllw-working-api and normalize results.
    """
    polygonurl = "https://zllw-working-api.p.rapidapi.com/search/bypolygon"

    houseresult = []
    print(f'Searching {status} homes in zone: {zone.zonename()}')

    interval = 1000
    minhomesize = 0
    maxhomesize = interval + minhomesize

    seen_ids = set()
    max_sqft = 10000
    min_interval = 20

    while True:
        lastpage = 1
        maxpage = 2
        maxpagebackup = 2
        results_in_this_interval = []
        should_restart = False

        while maxpage >= lastpage:
            querystring = {
                "polygon": zone.get_polygon_string(),
                "page": str(lastpage),
                "sortOrder": "Homes_for_you",
                "listingStatus": status,
                "bed_min": "No_Min",
                "bed_max": "No_Max",
                "bathrooms": "Any",
                "homeType": "Houses, Townhomes, Multi-family, Condos/Co-ops, Lots-Land, Apartments, Manufactured",
                "maxHOA": "Any",
                "listingType": "By_Agent",
                "listingTypeOptions": "Agent listed,New Construction,Fore-closures,Auctions",
                "parkingSpots": "Any",
                "mustHaveBasement": "No",
                "daysOnZillow": "Any",
                "soldInLast": soldInLast,
                "squareFeetRange": f"min:{str(minhomesize)}, max: {str(maxhomesize)}",
            }

            print(f"Search {minhomesize}–{maxhomesize} sqft, page {lastpage}, status={status}")
            response = requests.get(polygonurl, headers=headers, params=querystring)
            time.sleep(1.0)

            if response.status_code == 502:
                warn(f'502 error on {zone.zonename()}')
                should_restart = True
                break

            try:
                result = response.json()

                # Get pagination from new API structure
                total_results = result.get('resultsCount', 0)
                totalMatchingCount = total_results.get('totalMatchingCount', 0)
                print(f'{totalMatchingCount} for {minhomesize}–{maxhomesize} size.')

                if 'pagesInfo' in result:
                    maxpage = result['pagesInfo'].get('totalPages', 0)
                    if maxpage != 0:
                        maxpagebackup = maxpage

                # Get and normalize search results
                search_results = result.get('searchResults', [])
                for search_result in search_results:
                    normalized = normalize_brief_listing(search_result)
                    results_in_this_interval.append(normalized)

                print(f'Page {lastpage} of {maxpage} processed.')
                lastpage += 1

                if maxpage == 0:
                    maxpage = maxpagebackup
                    print('No results found.')

                if totalMatchingCount >= 1000:
                    print("Search too large for interval, reducing...")
                    interval = max(min_interval, interval // 2)
                    maxhomesize = minhomesize + interval
                    should_restart = True
                    break

            except Exception as e:
                print("Search Zillow failed due to an exception:", e)
                break

        if should_restart:
            continue

        if maxhomesize >= max_sqft:
            print("All intervals processed.")
            break

        for listing in results_in_this_interval:
            zpid = listing.get('zpid')
            if zpid and zpid not in seen_ids:
                seen_ids.add(zpid)
                houseresult.append(listing)
        print(f'Found {len(houseresult)} unique results Cummulatively.')

        minhomesize = maxhomesize
        maxhomesize = min(minhomesize + interval, max_sqft)

    return houseresult

def SearchZillowHomesFSBO(city, lastpage, maxpage, status="forSale", duration=14):
    """
    Search for 'For Sale By Owner' homes.
    Updated to use new zllw-working-api and normalize results.
    """
    url = "https://zllw-working-api.p.rapidapi.com/search/byaddress"

    # Map old status values to new API values
    status_mapping = {
        "forSale": "For_Sale",
        "recentlySold": "Recently_Sold",
        "sold": "Sold"
    }
    listing_status = status_mapping.get(status, "For_Sale")

    houseresult = []
    print('Search in location ' + status + ' : ', city)

    querystring = {
        "location": city + ", WA",
        "page": str(lastpage),
        "listingStatus": listing_status,
        "listingType": "By_Owner",
        "isForSaleByOwner": "true",
        "sortOrder": "Homes_for_you",
        "daysOnZillow": str(duration) if duration else "Any"
    }

    response = requests.get(url, headers=headers, params=querystring)
    time.sleep(0.5)

    if response.status_code == 502:
        raise Exception('502 on ' + city)

    try:
        result = response.json()

        # Get and normalize search results
        search_results = result.get('searchResults', [])
        for search_result in search_results:
            normalized = normalize_brief_listing(search_result)
            houseresult.append(normalized)

        # Get pagination from new API structure
        if 'pagesInfo' in result:
            maxpage = result['pagesInfo'].get('totalPages', 0)

        print('lastpage:' + str(lastpage) + ' out of ' + str(maxpage))
        lastpage = lastpage + 1

    except Exception as e:
        raise Exception(f"Search Zillow failed due to an exception: {e}")

    return houseresult, lastpage, maxpage







# def UpdateListfromLocation(location):
#     querystring = {"location":location + ", wa","status":"recentlySold","doz":"30"}
#     response = requests.get(url, headers=headers, params=querystring)
#     result = response.json()
#
#     houseresult = result['results']
#     i=1
#     while result['totalPages']>i:
#         querystring = {"location": location + ", wa", "page": str(i+1),"status": "recentlySold", "doz": "30"}
#         response = requests.get(url, headers=headers, params=querystring)
#         result = response.json()
#         houseresult = houseresult+ result['results']
#         i=i+1
#
#     dbmethods.SaveHouseSearchDataintoDB(houseresult)
#     return dbmethods.AllListigs()

# def addHomesToDB():
#     csv_file_path = 'path_to_your_csv_file.csv'
#
#     # Connect to the SQLite database
#     conn = sqlite3.connect('listings.db')
#     cursor = conn.cursor()
#
#     # Open the CSV file and read its contents
#     with open(csv_file_path, 'r') as csv_file:
#         csv_reader = csv.reader(csv_file)
#
#         # Skip header (if it exists)
#         next(csv_reader)
#
#         # Insert each row into the database
#         for row in csv_reader:
#             # Assuming the CSV columns match the database table columns
#             cursor.execute("INSERT INTO Listing (api_id, added_on) VALUES (?, ?)", (row[0], row[1]))
#
#     # Commit the changes and close the connection
#     conn.commit()
#     conn.close()





# def searchZillow():
#     with open('../../data.txt', "r") as file:
#         responseobject = json.load(file)
#
#     results = responseobject['results']
#     all_fields = set()
#     for result in results:
#         all_fields.update(result.keys())
#
#     # Step 2 & 3: Use these fields as the CSV headers and write each result to the CSV.
#     with open('../../data.csv', 'w', newline='') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=all_fields)
#         writer.writeheader()
#         for row in results:
#             writer.writerow(row)
#     return responseobject