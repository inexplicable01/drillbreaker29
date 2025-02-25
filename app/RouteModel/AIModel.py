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

def AIModel(brieflisting,  customer, propertydata):
    """
    API endpoint to evaluate a listing's match likelihood for a customer.
    """

    customer_descriptions = customer_description_controller.retrieve_all_descriptions(customer.id)

    # Format descriptions: Join them into a single string (fallback to default if empty)
    if customer_descriptions:
        customer_description_text = " | ".join(desc.description for desc in customer_descriptions)
    else:
        customer_description_text = "No additional details provided."
    if not brieflisting:
        return jsonify({"error": "Listing not found"}), 404

    # Prepare prompt for AI     # - Interested Neighborhoods: {', '.join(locations)}
    prompt = f"""
    Given the following customer preferences and real estate listing, rate how likely the customer is to like this listing on a scale from 0 to 100.
    Provide a short concise explanation, no more than 150 characters.  Use Broken language if you need to get the point across.

    Customer Details:
    - Name: {customer.name}
    - Budget: {customer.minprice} to {customer.maxprice} (Ideal: {customer.idealprice})
    - Preferred square footage: {customer.minsqft} to {customer.maxsqft} (Ideal: {customer.idealsqft})
    - Parking Space needed : {customer.parkingspaceneeded} 
   - Additional Customer Preferences: {customer_description_text}

    Listing Details:
    - Price: {brieflisting.price}
    - Square Footage: {brieflisting.livingArea}
    - Location: {brieflisting.city}, {brieflisting.state}, {brieflisting.zipcode}
    - Bedrooms: {brieflisting.bedrooms}
    - Bathrooms: {brieflisting.bathrooms}
    - Home Type: {brieflisting.homeType}
    - Lot Size: {brieflisting.lotAreaValue} {brieflisting.lotAreaUnit}
    - Zestimate: {brieflisting.zestimate}
    - Status: {brieflisting.homeStatus}
    - Days on Market: {brieflisting.daysOnZillow}
    - Listed on: {brieflisting.listtime}
    - Year Built : {brieflisting.yearBuilt}
    - Covered or Garage Space: {brieflisting.parkingSpaces}
    - Have driveway parking : {brieflisting.hasDrivewayParking}
    - Wayber Comments: {brieflisting.waybercomments}



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
