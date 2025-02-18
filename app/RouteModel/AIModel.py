import os
from openai import OpenAI
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import json
# import customerzonecontroller
from app.DBFunc.CustomerZoneController import customerzonecontroller
from app.DBFunc.BriefListingController import brieflistingcontroller

from app.DBFunc.BriefListingController import brieflistingcontroller

# Load API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_apiKey")
client = OpenAI(api_key=OPENAI_API_KEY)
# client = OpenAI()

def AIModel(zpid,  customer, locations):
    """
    API endpoint to evaluate a listing's match likelihood for a customer.
    """
    if not zpid:
        return jsonify({"error": "Missing ZPID"}), 400

    # Fetch listing details (this should be replaced with your actual database/API call)
    listing_details = brieflistingcontroller.get_listing_by_zpid(zpid)  # Implement this function

    if not listing_details:
        return jsonify({"error": "Listing not found"}), 404

    # Prepare prompt for AI     # - Interested Neighborhoods: {', '.join(locations)}
    prompt = f"""
    Given the following customer preferences and real estate listing, rate how likely the customer is to like this listing on a scale from 0 to 100.
    Provide a short explanation.

    Customer Details:
    - Name: {customer.name}
    - Budget: {customer.minprice} to {customer.maxprice} (Ideal: {customer.idealprice})
    - Preferred square footage: {customer.minsqft} to {customer.maxsqft} (Ideal: {customer.idealsqft})


    Listing Details:
    - Price: {listing_details.price}
    - Square Footage: {listing_details.livingArea}
    - Location: {listing_details.city}, {listing_details.state}, {listing_details.zipcode}
    - Bedrooms: {listing_details.bedrooms}
    - Bathrooms: {listing_details.bathrooms}
    - Home Type: {listing_details.homeType}
    - Lot Size: {listing_details.lotAreaValue} {listing_details.lotAreaUnit}
    - Zestimate: {listing_details.zestimate}
    - Status: {listing_details.homeStatus}
    - Days on Market: {listing_details.daysOnZillow}
    - Sold By: {listing_details.soldBy}
    - Wayber Comments: {listing_details.waybercomments}


    Response format:
    {{
        "likelihood_score": int,  # A score between 0 and 100
        "reason": "string"  # Brief reason for the score
    }}
    """

    # Send prompt to OpenAI API
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a real estate AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        print(completion.choices[0].message)





        ai_result = completion.choices[0].message.content
        return json.loads(ai_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
