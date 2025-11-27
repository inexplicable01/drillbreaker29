"""
Seller Property Analysis Model
Handles geocoding, comp finding, and regression analysis for Level 2 sellers.
"""
import os
import requests
import math
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from app.DBModels.BriefListing import BriefListing
from app.DBFunc.BriefListingController import brieflistingcontroller
from app.DBFunc.SellerPropertyAnalysisController import sellerpropertyanalysiscontroller
from app.DBFunc.CustomerController import Customer, customercontroller
from app.ZillowAPI.ZillowAPICall import SearchZillowByAddress
from app.config import RECENTLYSOLD
from app.extensions import db

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert address string to latitude/longitude using Google Geocoding API.

    Args:
        address: Full street address (e.g., "123 Main St, Seattle, WA 98101")

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    if not address:
        return None

    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == 'OK' and len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            print(f"Geocoding failed for {address}: {data.get('status', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
        return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in miles.

    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point

    Returns:
        Distance in miles
    """
    # Earth's radius in miles
    R = 3959.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def find_comps_within_radius(
    center_lat: float,
    center_lon: float,
    property_type: str,
    radius_miles: float = 2.0,
    max_days_old: int = 180
) -> List[BriefListing]:
    """
    Find comparable properties within a radius, filtered by property type.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        property_type: Property type to filter (e.g., 'SINGLE_FAMILY', 'TOWNHOUSE')
        radius_miles: Search radius in miles (default 2.0)
        max_days_old: Maximum age of sold listings in days (default 180)

    Returns:
        List of BriefListing objects within radius
    """
    # Calculate date cutoff
    cutoff_timestamp = int((datetime.utcnow() - timedelta(days=max_days_old)).timestamp())

    # Query all recently sold homes of the same property type
    all_comps = BriefListing.query.filter(
        BriefListing.homeStatus == RECENTLYSOLD,
        BriefListing.homeType == property_type,
        BriefListing.soldtime >= cutoff_timestamp,
        BriefListing.soldprice.isnot(None),
        BriefListing.livingArea.isnot(None),
        BriefListing.latitude.isnot(None),
        BriefListing.longitude.isnot(None)
    ).all()

    # Filter by distance
    comps_within_radius = []
    for comp in all_comps:
        try:
            distance = haversine_distance(
                center_lat, center_lon,
                float(comp.latitude), float(comp.longitude)
            )
            if distance <= radius_miles:
                comps_within_radius.append(comp)
        except (TypeError, ValueError) as e:
            print(f"Error calculating distance for zpid {comp.zpid}: {e}")
            continue

    print(f"Found {len(comps_within_radius)} comps within {radius_miles} miles")
    return comps_within_radius


def run_regression_analysis(comps: List[BriefListing]) -> Dict:
    """
    Run linear regression on comparable properties to estimate price.

    Uses features: living area (sqft), bedrooms, bathrooms, lot size
    Target: sold price

    Args:
        comps: List of comparable BriefListing objects

    Returns:
        Dictionary with regression results and statistics
    """
    if len(comps) < 5:
        return {
            'success': False,
            'error': f'Not enough comps for regression (found {len(comps)}, need at least 5)',
            'num_comps': len(comps)
        }

    # Prepare feature matrix and target vector
    X = []
    y = []
    valid_comps = []

    for comp in comps:
        try:
            # Only include comps with complete data
            if (comp.soldprice and comp.livingArea and
                comp.bedrooms and comp.bathrooms):

                features = [
                    float(comp.livingArea),
                    float(comp.bedrooms),
                    float(comp.bathrooms),
                    float(comp.lotAreaValue) if comp.lotAreaValue else 0.0
                ]
                X.append(features)
                y.append(float(comp.soldprice))
                valid_comps.append(comp)
        except (TypeError, ValueError) as e:
            print(f"Skipping comp zpid {comp.zpid} due to data error: {e}")
            continue

    if len(valid_comps) < 5:
        return {
            'success': False,
            'error': f'Not enough valid comps (found {len(valid_comps)}, need at least 5)',
            'num_comps': len(valid_comps)
        }

    X = np.array(X)
    y = np.array(y)

    # Fit linear regression
    model = LinearRegression()
    model.fit(X, y)

    # Calculate predictions and R²
    y_pred = model.predict(X)
    r_squared = r2_score(y, y_pred)

    # Calculate statistics
    median_price = int(np.median(y))
    mean_price = int(np.mean(y))
    std_price = int(np.std(y))

    # Calculate average features
    avg_sqft = np.mean([c.livingArea for c in valid_comps])
    avg_beds = np.mean([c.bedrooms for c in valid_comps])
    avg_baths = np.mean([c.bathrooms for c in valid_comps])
    avg_dom = np.mean([c.daysOnZillow for c in valid_comps if c.daysOnZillow])

    # Price per sqft statistics
    price_per_sqft_list = [c.soldprice / c.livingArea for c in valid_comps if c.livingArea > 0]
    median_price_per_sqft = np.median(price_per_sqft_list) if price_per_sqft_list else None

    return {
        'success': True,
        'model': model,
        'r_squared': float(r_squared),
        'num_comps': len(valid_comps),
        'valid_comps': valid_comps,
        'comp_zpids': [c.zpid for c in valid_comps],
        'median_comp_price': median_price,
        'mean_comp_price': mean_price,
        'std_comp_price': std_price,
        'avg_comp_sqft': float(avg_sqft),
        'avg_days_on_market': int(avg_dom) if avg_dom else None,
        'median_price_per_sqft': float(median_price_per_sqft) if median_price_per_sqft else None,
        'feature_names': ['livingArea', 'bedrooms', 'bathrooms', 'lotAreaValue'],
        'coefficients': model.coef_.tolist(),
        'intercept': float(model.intercept_)
    }


def predict_price_for_property(
    regression_result: Dict,
    living_area: float,
    bedrooms: float,
    bathrooms: float,
    lot_area: float = 0.0
) -> Dict:
    """
    Use regression model to predict price for a specific property.

    Args:
        regression_result: Output from run_regression_analysis
        living_area: Square footage
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms
        lot_area: Lot size (optional)

    Returns:
        Dictionary with predicted price and confidence interval
    """
    if not regression_result['success']:
        return {
            'success': False,
            'error': regression_result['error']
        }

    model = regression_result['model']
    features = np.array([[living_area, bedrooms, bathrooms, lot_area]])

    predicted_price = int(model.predict(features)[0])

    # Calculate 95% confidence interval (rough estimate: ±2 std deviations)
    std_price = regression_result['std_comp_price']
    confidence_margin = int(1.96 * std_price)  # 95% CI

    confidence_lower = predicted_price - confidence_margin
    confidence_upper = predicted_price + confidence_margin

    price_per_sqft = predicted_price / living_area if living_area > 0 else None

    return {
        'success': True,
        'predicted_price': predicted_price,
        'confidence_lower': max(0, confidence_lower),  # Don't go below 0
        'confidence_upper': confidence_upper,
        'price_per_sqft': price_per_sqft,
        'r_squared': regression_result['r_squared']
    }


def get_seller_property_data(customer: Customer) -> Optional[Dict]:
    """
    Hybrid lookup: Try database first (by seller_zpid), then fall back to Zillow API.

    Args:
        customer: Customer object (Level 2 seller)

    Returns:
        Dictionary with property data or None if lookup fails
    """
    # Step 1: Try to find property in BriefListing by seller_zpid
    if customer.seller_zpid:
        print(f"Looking up property by seller_zpid: {customer.seller_zpid}")
        property_listing = BriefListing.query.filter_by(zpid=customer.seller_zpid).first()

        if property_listing:
            print(f"Found property in database: {property_listing.pleasant_address()}")
            return {
                'source': 'database',
                'zpid': property_listing.zpid,
                'address': property_listing.pleasant_address(),
                'property_type': property_listing.homeType,
                'living_area': float(property_listing.livingArea),
                'bedrooms': float(property_listing.bedrooms),
                'bathrooms': float(property_listing.bathrooms),
                'lot_area': float(property_listing.lotAreaValue) if property_listing.lotAreaValue else 0.0,
                'latitude': float(property_listing.latitude),
                'longitude': float(property_listing.longitude)
            }

    # Step 2: Fall back to address lookup
    if not customer.seller_streetaddress:
        print(f"No seller address found for customer {customer.id}")
        return None

    print(f"Property not in database, searching Zillow API for: {customer.seller_streetaddress}")

    # Try Zillow API lookup by address
    try:
        zillow_data = SearchZillowByAddress(customer.seller_streetaddress)

        if not zillow_data:
            print(f"Zillow API returned no data for {customer.seller_streetaddress}")
            return None

        # Extract property data from Zillow response
        zpid = zillow_data.get('zpid')
        property_type = zillow_data.get('homeType')
        living_area = zillow_data.get('livingArea')
        bedrooms = zillow_data.get('bedrooms')
        bathrooms = zillow_data.get('bathrooms')
        lot_area = zillow_data.get('lotAreaValue', 0.0)
        latitude = zillow_data.get('latitude')
        longitude = zillow_data.get('longitude')

        # Validate required fields
        if not all([zpid, property_type, living_area, bedrooms, bathrooms, latitude, longitude]):
            print(f"Missing required fields from Zillow API for {customer.seller_streetaddress}")
            return None

        # Save zpid back to customer for future lookups
        if zpid and not customer.seller_zpid:
            customer.seller_zpid = zpid
            db.session.commit()
            print(f"Saved seller_zpid {zpid} to customer {customer.id}")

        return {
            'source': 'zillow_api',
            'zpid': zpid,
            'address': customer.seller_streetaddress,
            'property_type': property_type,
            'living_area': float(living_area),
            'bedrooms': float(bedrooms),
            'bathrooms': float(bathrooms),
            'lot_area': float(lot_area),
            'latitude': float(latitude),
            'longitude': float(longitude)
        }

    except Exception as e:
        print(f"Error fetching property data from Zillow API: {e}")
        return None


def analyze_seller_property_for_customer(customer: Customer, radius_miles: float = 2.0) -> Dict:
    """
    Complete analysis workflow for a Level 2 seller using hybrid lookup.

    Args:
        customer: Customer object (Level 2 seller)
        radius_miles: Comp search radius (default 2.0 miles)

    Returns:
        Dictionary with complete analysis results
    """
    # Step 1: Get property data (database or API)
    property_data = get_seller_property_data(customer)

    if not property_data:
        return {
            'success': False,
            'error': f'Could not find property data for customer {customer.id}',
            'customer_id': customer.id
        }

    print(f"Using property data from {property_data['source']}: {property_data['address']}")

    # Step 2: Find comps within radius
    comps = find_comps_within_radius(
        property_data['latitude'],
        property_data['longitude'],
        property_data['property_type'],
        radius_miles
    )

    if len(comps) < 5:
        return {
            'success': False,
            'error': f'Not enough comps found (found {len(comps)}, need at least 5)',
            'customer_id': customer.id,
            'num_comps': len(comps)
        }

    # Step 3: Run regression on comps
    regression_result = run_regression_analysis(comps)

    if not regression_result['success']:
        return {
            'success': False,
            'error': regression_result['error'],
            'customer_id': customer.id
        }

    # Step 4: Predict price for this property
    prediction = predict_price_for_property(
        regression_result,
        property_data['living_area'],
        property_data['bedrooms'],
        property_data['bathrooms'],
        property_data['lot_area']
    )

    if not prediction['success']:
        return {
            'success': False,
            'error': prediction['error'],
            'customer_id': customer.id
        }

    # Step 5: Save to database
    analysis = sellerpropertyanalysiscontroller.create_analysis(
        customer_id=customer.id,
        seller_address=property_data['address'],
        latitude=property_data['latitude'],
        longitude=property_data['longitude'],
        property_type=property_data['property_type'],
        num_comps=regression_result['num_comps'],
        comp_zpids=regression_result['comp_zpids'],
        predicted_price=prediction['predicted_price'],
        price_per_sqft=prediction['price_per_sqft'],
        confidence_lower=prediction['confidence_lower'],
        confidence_upper=prediction['confidence_upper'],
        r_squared=prediction['r_squared'],
        median_comp_price=regression_result['median_comp_price'],
        avg_comp_sqft=regression_result['avg_comp_sqft'],
        avg_days_on_market=regression_result['avg_days_on_market'],
        median_price_per_sqft=regression_result['median_price_per_sqft'],
        model_features={
            'living_area': property_data['living_area'],
            'bedrooms': property_data['bedrooms'],
            'bathrooms': property_data['bathrooms'],
            'lot_area': property_data['lot_area']
        }
    )

    return {
        'success': True,
        'customer_id': customer.id,
        'analysis_id': analysis.id,
        'property_data': property_data,
        'predicted_price': prediction['predicted_price'],
        'confidence_lower': prediction['confidence_lower'],
        'confidence_upper': prediction['confidence_upper'],
        'price_per_sqft': prediction['price_per_sqft'],
        'r_squared': prediction['r_squared'],
        'num_comps': regression_result['num_comps'],
        'median_comp_price': regression_result['median_comp_price'],
        'avg_days_on_market': regression_result['avg_days_on_market'],
        'week_over_week_change_pct': analysis.week_over_week_change_pct,
        'week_over_week_change_dollars': analysis.week_over_week_change_dollars
    }


def analyze_seller_property(
    customer_id: int,
    seller_address: str,
    property_type: str,
    living_area: float,
    bedrooms: float,
    bathrooms: float,
    lot_area: float = 0.0,
    radius_miles: float = 2.0
) -> Dict:
    """
    Complete analysis workflow for a Level 2 seller's property.

    Args:
        customer_id: Customer ID
        seller_address: Full property address
        property_type: Property type (SINGLE_FAMILY, TOWNHOUSE, etc.)
        living_area: Square footage
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms
        lot_area: Lot size (optional)
        radius_miles: Comp search radius (default 2.0 miles)

    Returns:
        Dictionary with complete analysis results
    """
    # Step 1: Geocode the address
    coords = geocode_address(seller_address)
    if not coords:
        return {
            'success': False,
            'error': f'Failed to geocode address: {seller_address}'
        }

    lat, lon = coords
    print(f"Geocoded {seller_address} to ({lat}, {lon})")

    # Step 2: Find comps within radius
    comps = find_comps_within_radius(lat, lon, property_type, radius_miles)

    if len(comps) < 5:
        return {
            'success': False,
            'error': f'Not enough comps found (found {len(comps)}, need at least 5)',
            'latitude': lat,
            'longitude': lon,
            'num_comps': len(comps)
        }

    # Step 3: Run regression on comps
    regression_result = run_regression_analysis(comps)

    if not regression_result['success']:
        return {
            'success': False,
            'error': regression_result['error'],
            'latitude': lat,
            'longitude': lon,
            'num_comps': len(comps)
        }

    # Step 4: Predict price for this property
    prediction = predict_price_for_property(
        regression_result,
        living_area,
        bedrooms,
        bathrooms,
        lot_area
    )

    if not prediction['success']:
        return {
            'success': False,
            'error': prediction['error'],
            'latitude': lat,
            'longitude': lon
        }

    # Step 5: Save to database
    analysis = sellerpropertyanalysiscontroller.create_analysis(
        customer_id=customer_id,
        seller_address=seller_address,
        latitude=lat,
        longitude=lon,
        property_type=property_type,
        num_comps=regression_result['num_comps'],
        comp_zpids=regression_result['comp_zpids'],
        predicted_price=prediction['predicted_price'],
        price_per_sqft=prediction['price_per_sqft'],
        confidence_lower=prediction['confidence_lower'],
        confidence_upper=prediction['confidence_upper'],
        r_squared=prediction['r_squared'],
        median_comp_price=regression_result['median_comp_price'],
        avg_comp_sqft=regression_result['avg_comp_sqft'],
        avg_days_on_market=regression_result['avg_days_on_market'],
        median_price_per_sqft=regression_result['median_price_per_sqft'],
        model_features={
            'living_area': living_area,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'lot_area': lot_area
        }
    )

    return {
        'success': True,
        'analysis_id': analysis.id,
        'predicted_price': prediction['predicted_price'],
        'confidence_lower': prediction['confidence_lower'],
        'confidence_upper': prediction['confidence_upper'],
        'price_per_sqft': prediction['price_per_sqft'],
        'r_squared': prediction['r_squared'],
        'num_comps': regression_result['num_comps'],
        'median_comp_price': regression_result['median_comp_price'],
        'avg_days_on_market': regression_result['avg_days_on_market'],
        'week_over_week_change_pct': analysis.week_over_week_change_pct,
        'week_over_week_change_dollars': analysis.week_over_week_change_dollars,
        'latitude': lat,
        'longitude': lon
    }