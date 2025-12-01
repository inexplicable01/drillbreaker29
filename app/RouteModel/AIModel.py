import os
from openai import OpenAI
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import json

#from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.DBFunc.CustomerDescriptionController import customer_description_controller

#from app.DBFunc.BriefListingController import brieflistingcontroller

# Load API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_apiKey")
client = OpenAI(api_key=OPENAI_API_KEY)
# client = OpenAI()

def AIModel(brieflisting, customer, propertydata, customer_zone_names=None, listing_zone_name=None, is_in_preferred_zone=False):
    """
    API endpoint to evaluate a listing's match likelihood for a customer.

    Args:
        brieflisting: BriefListing object
        customer: Customer object
        propertydata: Property data dict
        customer_zone_names: List of zone names the customer is interested in
        listing_zone_name: Zone name of the listing
        is_in_preferred_zone: Boolean indicating if listing is in customer's preferred zones
    """

    customer_descriptions = customer_description_controller.retrieve_all_descriptions(customer.id)

    # Format descriptions: Join them into a single string (fallback to default if empty)
    if customer_descriptions:
        customer_description_text = " | ".join(desc.description for desc in customer_descriptions)
    else:
        customer_description_text = "No additional details provided."
    if not brieflisting:
        return jsonify({"error": "Listing not found"}), 404

    # Format zone information
    customer_zone_names = customer_zone_names or []
    listing_zone_name = listing_zone_name or "Unknown"
    zone_match_status = "MATCH! In preferred zone" if is_in_preferred_zone else "NOT in preferred zones"

    # Calculate market positioning metrics
    price_to_zestimate_ratio = None
    price_positioning = "Unknown"
    if brieflisting.price and brieflisting.zestimate and brieflisting.zestimate > 0:
        price_to_zestimate_ratio = (brieflisting.price / brieflisting.zestimate) * 100
        if price_to_zestimate_ratio < 95:
            price_positioning = f"DEAL! Listed {100 - price_to_zestimate_ratio:.0f}% below Zestimate"
        elif price_to_zestimate_ratio > 105:
            price_positioning = f"Overpriced {price_to_zestimate_ratio - 100:.0f}% above Zestimate"
        else:
            price_positioning = "Priced at market value"

    # Budget fit analysis
    budget_fit = "Unknown"
    if customer.minprice and customer.maxprice and brieflisting.price:
        if brieflisting.price < customer.minprice:
            budget_fit = f"Below budget by ${customer.minprice - brieflisting.price:,}"
        elif brieflisting.price > customer.maxprice:
            budget_fit = f"Over budget by ${brieflisting.price - customer.maxprice:,}"
        elif customer.idealprice:
            diff = abs(brieflisting.price - customer.idealprice)
            budget_fit = f"Within range, ${diff:,} from ideal"
        else:
            budget_fit = "Within budget range"

    # Size fit analysis
    size_fit = "Unknown"
    if customer.minsqft and customer.maxsqft and brieflisting.livingArea:
        if brieflisting.livingArea < customer.minsqft:
            size_fit = f"Too small by {customer.minsqft - brieflisting.livingArea:,.0f} sqft"
        elif brieflisting.livingArea > customer.maxsqft:
            size_fit = f"Too large by {brieflisting.livingArea - customer.maxsqft:,.0f} sqft"
        elif customer.idealsqft:
            diff = abs(brieflisting.livingArea - customer.idealsqft)
            size_fit = f"Within range, {diff:,.0f} sqft from ideal"
        else:
            size_fit = "Within size range"

    # Prepare improved prompt with scoring rubric
    prompt = f"""
You are evaluating how well this listing matches a buyer's preferences. Score from 0-100 using this rubric:

SCORING GUIDE:
- 0-20: Poor match (major dealbreakers: way over budget, wrong size, missing critical features)
- 21-40: Weak match (several significant mismatches)
- 41-60: Decent match (meets basic requirements but not ideal)
- 61-80: Good match (meets most preferences well)
- 81-100: Excellent match (hits ideal preferences, great value, perfect fit)

CUSTOMER PREFERENCES:
- Budget: ${customer.minprice:,} to ${customer.maxprice:,} (Ideal: ${customer.idealprice:,})
  → Budget Fit: {budget_fit}
- Square Footage: {customer.minsqft:,} to {customer.maxsqft:,} sqft (Ideal: {customer.idealsqft:,})
  → Size Fit: {size_fit}
- Parking Spaces Needed: {customer.parkingspaceneeded}
- Preferred Zones/Neighborhoods: {', '.join(customer_zone_names) if customer_zone_names else 'No specific zone preferences'}
- Additional Preferences: {customer_description_text}

LISTING DETAILS:
- Price: ${brieflisting.price:,}
- Zestimate: ${brieflisting.zestimate:,}
  → Market Position: {price_positioning}
- Square Footage: {brieflisting.livingArea:,} sqft
- Location: {brieflisting.city}, {brieflisting.state} {brieflisting.zipcode}
- Zone/Neighborhood: {listing_zone_name}
  → Zone Match: {zone_match_status}
- Bedrooms: {brieflisting.bedrooms} | Bathrooms: {brieflisting.bathrooms}
- Home Type: {brieflisting.homeType}
- Lot Size: {brieflisting.lotAreaValue} {brieflisting.lotAreaUnit}
- Year Built: {brieflisting.yearBuilt}
- Parking: {brieflisting.parkingSpaces} garage/covered spaces, Driveway: {brieflisting.hasDrivewayParking}
- Days on Market: {brieflisting.daysOnZillow} days
- Internal Notes: {brieflisting.waybercomments}

EVALUATION CRITERIA:
1. Price fit (20 pts): How well does price match budget? Is it a good deal vs Zestimate?
2. Size fit (20 pts): Does square footage match preferences?
3. Location (15 pts): Good neighborhood for customer?
4. Features (15 pts): Parking, bedrooms, bathrooms match needs?
5. Value (15 pts): Price positioning, days on market, condition
6. Overall fit (15 pts): Matches additional preferences & lifestyle?

Provide your evaluation in this EXACT JSON format:
{{
    "likelihood_score": <integer 0-100>,
    "reason": "<VERY concise explanation, max 150 characters, ok to use shorthand>"
}}

Be honest and critical. Use the full 0-100 range. Keep reason brief but informative.
"""

    # Send prompt to OpenAI API with consistency controls
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,  # Lower temperature for more consistent scoring
            messages=[
                {"role": "system", "content": "You are an expert real estate matching AI. You evaluate listings objectively and score them accurately based on buyer preferences. You are concise and honest."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}  # Enforce JSON response
        )

        print(completion.choices[0].message)

        ai_result = completion.choices[0].message.content
        result = json.loads(ai_result)

        # Validate result structure
        if "likelihood_score" not in result or "reason" not in result:
            raise ValueError("Invalid response format from AI")

        # Ensure score is in valid range
        result["likelihood_score"] = max(0, min(100, int(result["likelihood_score"])))

        # Trim reason to 150 characters if needed
        if len(result["reason"]) > 150:
            result["reason"] = result["reason"][:147] + "..."

        return result

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {ai_result}")
        # Fallback response
        return {
            "likelihood_score": 50,
            "reason": "Error: Could not parse AI response"
        }
    except Exception as e:
        print(f"AI Model error: {e}")
        return jsonify({"error": str(e)}), 500
