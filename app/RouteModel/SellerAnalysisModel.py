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
from app.GraphTools.plt_plots import createSellerPriceTrendPlot
from pathlib import Path

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


def calculate_comp_similarity_score(
    comp: BriefListing,
    subject_beds: float,
    subject_baths: float,
    subject_sqft: float,
    subject_year_built: int = None,
    subject_parking: int = None,
    subject_lot_size: float = None
) -> float:
    """
    Calculate similarity score between a comp and the subject property.
    Lower score = more similar.

    Weights (can be adjusted):
    - Bedrooms: 20%
    - Bathrooms: 15%
    - Square footage: 35%
    - Year built: 20%
    - Parking: 5%
    - Lot size: 5%
    """
    score = 0.0

    # Bedroom difference (weight: 20%)
    if comp.bedrooms:
        bed_diff = abs(float(comp.bedrooms) - subject_beds) / max(subject_beds, 1)
        score += bed_diff * 20

    # Bathroom difference (weight: 15%)
    if comp.bathrooms:
        bath_diff = abs(float(comp.bathrooms) - subject_baths) / max(subject_baths, 1)
        score += bath_diff * 15

    # Square footage difference (weight: 35%)
    if comp.livingArea and subject_sqft:
        sqft_diff = abs(float(comp.livingArea) - subject_sqft) / subject_sqft
        score += sqft_diff * 35

    # Year built difference (weight: 20%)
    if subject_year_built and comp.yearBuilt:
        try:
            year_diff = abs(int(comp.yearBuilt) - subject_year_built) / 100.0  # Normalize to ~1 for 100 year difference
            score += year_diff * 20
        except (ValueError, TypeError):
            pass

    # Parking spaces difference (weight: 5%)
    if subject_parking is not None and comp.parkingSpaces:
        try:
            parking_diff = abs(int(comp.parkingSpaces) - subject_parking) / max(subject_parking, 1)
            score += parking_diff * 5
        except (ValueError, TypeError):
            pass

    # Lot size difference (weight: 5%)
    if subject_lot_size and comp.lotAreaValue:
        try:
            lot_diff = abs(float(comp.lotAreaValue) - subject_lot_size) / max(subject_lot_size, 1)
            score += lot_diff * 5
        except (ValueError, TypeError):
            pass

    return score


def find_comps_within_radius(
    center_lat: float,
    center_lon: float,
    property_type: str,
    subject_beds: float = None,
    subject_baths: float = None,
    subject_sqft: float = None,
    subject_year_built: int = None,
    subject_parking: int = None,
    subject_lot_size: float = None,
    radius_miles: float = 2.0,
    max_days_old: int = 180,
    max_comps: int = 20,
    use_similarity_ranking: bool = True
) -> List[BriefListing]:
    """
    Find comparable properties within a radius, with similarity ranking.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        property_type: Property type to filter (e.g., 'SINGLE_FAMILY', 'TOWNHOUSE')
        subject_beds: Subject property bedrooms (for similarity scoring)
        subject_baths: Subject property bathrooms (for similarity scoring)
        subject_sqft: Subject property square footage (for similarity scoring)
        subject_year_built: Subject property year built (optional)
        subject_parking: Subject property parking spaces (optional)
        subject_lot_size: Subject property lot size (optional)
        radius_miles: Search radius in miles (default 2.0)
        max_days_old: Maximum age of sold listings in days (default 180)
        max_comps: Maximum number of comps to return (default 20)
        use_similarity_ranking: Whether to rank by similarity (default True)

    Returns:
        List of BriefListing objects, optionally ranked by similarity
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

    # Filter by distance and collect comps with similarity scores
    comps_with_scores = []
    for comp in all_comps:
        try:
            distance = haversine_distance(
                center_lat, center_lon,
                float(comp.latitude), float(comp.longitude)
            )
            if distance <= radius_miles:
                # Calculate similarity score if we have subject property data
                if use_similarity_ranking and subject_beds and subject_baths and subject_sqft:
                    similarity_score = calculate_comp_similarity_score(
                        comp=comp,
                        subject_beds=subject_beds,
                        subject_baths=subject_baths,
                        subject_sqft=subject_sqft,
                        subject_year_built=subject_year_built,
                        subject_parking=subject_parking,
                        subject_lot_size=subject_lot_size
                    )
                    comps_with_scores.append((comp, similarity_score, distance))
                else:
                    comps_with_scores.append((comp, 0, distance))
        except (TypeError, ValueError) as e:
            print(f"Error calculating distance for zpid {comp.zpid}: {e}")
            continue

    # Sort by similarity score (lower is better)
    if use_similarity_ranking and subject_beds and subject_baths and subject_sqft:
        comps_with_scores.sort(key=lambda x: x[1])  # Sort by similarity score
        print(f"Found {len(comps_with_scores)} comps within {radius_miles} miles, ranked by similarity")
    else:
        comps_with_scores.sort(key=lambda x: x[2])  # Sort by distance
        print(f"Found {len(comps_with_scores)} comps within {radius_miles} miles, sorted by distance")

    # Limit to max_comps
    comps_with_scores = comps_with_scores[:max_comps]

    # Extract just the BriefListing objects
    comps_within_radius = [comp for comp, score, dist in comps_with_scores]

    # Log the top 5 comps for debugging
    if comps_with_scores and use_similarity_ranking:
        print("\nTop 5 most similar comps:")
        for i, (comp, score, dist) in enumerate(comps_with_scores[:5]):
            print(f"  {i+1}. {comp.pleasant_address()} - Score: {score:.2f}, Distance: {dist:.2f}mi, "
                  f"Beds: {comp.bedrooms}, Baths: {comp.bathrooms}, Sqft: {comp.livingArea}")

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

    # Step 2: Find comps within radius using similarity ranking
    comps = find_comps_within_radius(
        center_lat=property_data['latitude'],
        center_lon=property_data['longitude'],
        property_type=property_data['property_type'],
        subject_beds=property_data['bedrooms'],
        subject_baths=property_data['bathrooms'],
        subject_sqft=property_data['living_area'],
        subject_lot_size=property_data.get('lot_area'),
        radius_miles=radius_miles,
        use_similarity_ranking=True
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

def generate_seller_price_trend_chart(customer_id: int, weeks: int = 12) -> Optional[str]:
    """
    Generate and save a price trend chart for a Level 2 seller.

    Args:
        customer_id: Customer ID
        weeks: Number of weeks of history to plot (default 12)

    Returns:
        Path to the saved chart file, or None if no data available
    """
    # Get customer info
    customer = customercontroller.getCustomerByID(customer_id)
    if not customer:
        print(f"Customer {customer_id} not found")
        return None

    # Get historical analyses
    analyses = sellerpropertyanalysiscontroller.get_historical_trend(customer_id, weeks=weeks)

    if not analyses or len(analyses) == 0:
        print(f"No analysis data found for customer {customer_id}")
        return None

    # Create output directory if it doesn't exist
    output_dir = Path("app/static/seller_analysis_charts")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = f"seller_trend_{customer_id}.png"
    filepath = output_dir / filename

    # Create the chart
    customer_name = f"{customer.name} {customer.lastname or ''}".strip()
    chart_data = createSellerPriceTrendPlot(
        analyses=analyses,
        customer_name=customer_name,
        savefilepath=str(filepath)
    )

    if chart_data:
        print(f"Price trend chart generated for customer {customer_id}: {filepath}")
        return str(filepath)
    else:
        print(f"Failed to generate chart for customer {customer_id}")
        return None


def get_seller_chart_url(customer_id: int, base_url: str = "https://www.drillbreaker29.com") -> Optional[str]:
    """
    Get the public URL for a seller's price trend chart.

    Args:
        customer_id: Customer ID
        base_url: Base URL of the application

    Returns:
        Public URL to the chart image, or None if chart doesn't exist
    """
    chart_path = Path(f"app/static/seller_analysis_charts/seller_trend_{customer_id}.png")

    if chart_path.exists():
        return f"{base_url}/static/seller_analysis_charts/seller_trend_{customer_id}.png"
    else:
        return None
