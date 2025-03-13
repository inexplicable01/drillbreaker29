# email_bp.py
from flask import Blueprint, render_template
from app.DBModels.BriefListing import BriefListing
from app.config import SW, FOR_SALE
# from flask import Flask, render_template, make_response
# from weasyprint import HTML
from app.ZillowAPI.ZillowDataProcessor import loadPropertyDataFromBrief
from app.DBFunc.CachedInvestmentController import cachedinvestmentdatacontroller, CachedInvestmentData
import pandas as pd
import time
from datetime import datetime, timedelta
# import ace_tools as tools  # Assuming ace_tools is available for displaying tables

from datetime import datetime

investmentclients_bp = Blueprint('investmentclients_bp', __name__, url_prefix='/investmentclients')

@investmentclients_bp.route('/table', methods=['GET','POST'])
def table():
    return render_template("InvestmentPage.html")


@investmentclients_bp.route('/aparna', methods=['GET', 'POST'])
def aparna():
    customer_id = 112  # Hardcoded customer ID, should be dynamic

    # Define cash flow parameters
    PROPERTY_TAX_RATE = 0.0108
    INSURANCE_RATE = 1200  # Annual insurance cost
    MAINTENANCE_RATE = 0.01  # 1% of price annually
    RENTAL_YIELD = 0.06  # 6% of property price as yearly rent
    MORTGAGE_RATE = 0.07  # 7% interest rate
    LOAN_TERM_YEARS = 30
    LOAN_TO_VALUE = 0.75  # 75% loan, 25% down payment

    # Query listings matching base criteria
    query = BriefListing.query.filter(
        BriefListing.search_neigh == 'Renton',
        BriefListing.homeStatus == FOR_SALE,
        BriefListing.price < 500000
    )

    listings_data = []
    for listing in query:
        # Check if the listing is already cached
        cached_data = cachedinvestmentdatacontroller.get_cached_listing(listing.zpid, customer_id)
        if cached_data:
            cached_data['hdpUrl']=listing.hdpUrl
            listings_data.append(cached_data)
            continue  # Skip recalculating

        # Skip manufactured homes or land
        if hasattr(listing, "homeType") and listing.homeType in ["MANUFACTURED", "LOT"]:
            continue

        try:
            # Load property details
            propertydetails = loadPropertyDataFromBrief(listing)
            taxAnnualAmount = propertydetails['resoFacts'].get('taxAnnualAmount', 0)
            price = listing.price

            print('===== Processing Listing =====')
            print(f'Price: {price} | Tax from propertydetails: {taxAnnualAmount}')

            monthlyHoaFee = 0  # Default HOA Fee

            # Ensure HOA fee exists before accessing
            if "monthlyHoaFee" in propertydetails and propertydetails["monthlyHoaFee"]:
                monthlyHoaFee = propertydetails["monthlyHoaFee"]

            # Loan calculations
            loan_amount = price * LOAN_TO_VALUE
            assessed_value = listing.taxAssessedValue or price
            estimated_rent = listing.rentZestimate or (price * RENTAL_YIELD / 12)

            monthly_interest_rate = MORTGAGE_RATE / 12
            num_payments = LOAN_TERM_YEARS * 12
            monthly_mortgage = (loan_amount * monthly_interest_rate) / (
                1 - (1 + monthly_interest_rate) ** -num_payments
            )

            # Monthly expenses
            property_tax = (assessed_value * PROPERTY_TAX_RATE) / 12
            insurance = INSURANCE_RATE / 12
            maintenance = (price * MAINTENANCE_RATE) / 12

            # Total expenses and cash flow
            total_expenses = monthly_mortgage + property_tax + insurance + maintenance + monthlyHoaFee
            cash_flow = estimated_rent - total_expenses

            # Store in database cache
            cachedinvestmentdatacontroller.adddata(
                zpid=listing.zpid,
                customer_id=customer_id,
                mls=listing.NWMLS_id,
                address=str(listing),
                price=price,
                estimated_rent=estimated_rent,
                mortgage=monthly_mortgage,
                property_tax=property_tax,
                hoa_fee=monthlyHoaFee,
                insurance=insurance,
                maintenance=maintenance,
                cash_flow=cash_flow,
            )

            # Append listing data
            listings_data.append({
                'zpid': listing.zpid,
                'mls': listing.NWMLS_id,
                'address': str(listing),
                'hdpUrl' :listing.hdpUrl,
                'price': f"${price:,.2f}",
                'estimated_rent': f"${estimated_rent:,.2f}",
                'mortgage': f"${monthly_mortgage:,.2f}",
                'property_tax': f"${property_tax:,.2f}",
                'hoa_fee': f"${monthlyHoaFee:,.2f}",
                'insurance': f"${insurance:,.2f}",
                'maintenance': f"${maintenance:,.2f}",
                'cash_flow': f"${cash_flow:,.2f}"
            })

            time.sleep(0.5)

        except Exception as e:
            print(f"Error processing listing {listing.zpid}: {str(e)}")
            continue

    # Sort all listings by cash flow (highest to lowest)
    listings_data.sort(key=lambda x: float(x['cash_flow'].replace("$", "").replace(",", "")), reverse=True)

    # Convert to Pandas DataFrame for easy visualization
    df = pd.DataFrame(listings_data)

    # Display DataFrame in a table format (if using a tool like Ace Tools)
    # tools.display_dataframe_to_user(name="Sorted Listings by Cash Flow", dataframe=df)

    return render_template("investment_templates/aparna_listings.html", listings=listings_data)

@investmentclients_bp.route('/sunny', methods=['GET', 'POST'])
def sunny():
    customer_id = 120  # Hardcoded customer ID, should be dynamic

    # Define cash flow parameters
    PROPERTY_TAX_RATE = 0.0108
    INSURANCE_RATE = 1200  # Annual insurance cost
    MAINTENANCE_RATE = 0.01  # 1% of price annually
    RENTAL_YIELD = 0.06  # 6% of property price as yearly rent
    MORTGAGE_RATE = 0.07  # 7% interest rate
    LOAN_TERM_YEARS = 30
    LOAN_TO_VALUE = 0.75  # 75% loan, 25% down payment

    # Query listings matching base criteria
    query = BriefListing.query.filter(
        BriefListing.search_neigh == 'Lynnwood',
        BriefListing.homeStatus == FOR_SALE,
        BriefListing.price < 500000
    )

    listings_data = []
    for listing in query:
        # Check if the listing is already cached
        cached_data = cachedinvestmentdatacontroller.get_cached_listing(listing.zpid, customer_id)
        if cached_data:
            cached_data['hdpUrl']=listing.hdpUrl
            listings_data.append(cached_data)
            continue  # Skip recalculating

        # Skip manufactured homes or land
        if hasattr(listing, "homeType") and listing.homeType in ["MANUFACTURED", "LOT"]:
            continue

        try:
            # Load property details
            propertydetails = loadPropertyDataFromBrief(listing)
            taxAnnualAmount = propertydetails['resoFacts'].get('taxAnnualAmount', 0)
            price = listing.price

            print('===== Processing Listing =====')
            print(f'Price: {price} | Tax from propertydetails: {taxAnnualAmount}')

            monthlyHoaFee = 0  # Default HOA Fee

            # Ensure HOA fee exists before accessing
            if "monthlyHoaFee" in propertydetails and propertydetails["monthlyHoaFee"]:
                monthlyHoaFee = propertydetails["monthlyHoaFee"]

            # Loan calculations
            loan_amount = price * LOAN_TO_VALUE
            assessed_value = listing.taxAssessedValue or price
            estimated_rent = listing.rentZestimate or (price * RENTAL_YIELD / 12)

            monthly_interest_rate = MORTGAGE_RATE / 12
            num_payments = LOAN_TERM_YEARS * 12
            monthly_mortgage = (loan_amount * monthly_interest_rate) / (
                1 - (1 + monthly_interest_rate) ** -num_payments
            )

            # Monthly expenses
            property_tax = (assessed_value * PROPERTY_TAX_RATE) / 12
            insurance = INSURANCE_RATE / 12
            maintenance = (price * MAINTENANCE_RATE) / 12

            # Total expenses and cash flow
            total_expenses = monthly_mortgage + property_tax + insurance + maintenance + monthlyHoaFee
            cash_flow = estimated_rent - total_expenses

            # Store in database cache
            cachedinvestmentdatacontroller.adddata(
                zpid=listing.zpid,
                customer_id=customer_id,
                mls=listing.NWMLS_id,
                address=str(listing),
                price=price,
                estimated_rent=estimated_rent,
                mortgage=monthly_mortgage,
                property_tax=property_tax,
                hoa_fee=monthlyHoaFee,
                insurance=insurance,
                maintenance=maintenance,
                cash_flow=cash_flow,
            )

            # Append listing data
            listings_data.append({
                'zpid': listing.zpid,
                'mls': listing.NWMLS_id,
                'address': str(listing),
                'hdpUrl' :listing.hdpUrl,
                'price': f"${price:,.2f}",
                'estimated_rent': f"${estimated_rent:,.2f}",
                'mortgage': f"${monthly_mortgage:,.2f}",
                'property_tax': f"${property_tax:,.2f}",
                'hoa_fee': f"${monthlyHoaFee:,.2f}",
                'insurance': f"${insurance:,.2f}",
                'maintenance': f"${maintenance:,.2f}",
                'cash_flow': f"${cash_flow:,.2f}"
            })

            time.sleep(0.5)

        except Exception as e:
            print(f"Error processing listing {listing.zpid}: {str(e)}")
            continue

    # Sort all listings by cash flow (highest to lowest)
    listings_data.sort(key=lambda x: float(x['cash_flow'].replace("$", "").replace(",", "")), reverse=True)

    # Convert to Pandas DataFrame for easy visualization
    df = pd.DataFrame(listings_data)

    # Display DataFrame in a table format (if using a tool like Ace Tools)
    # tools.display_dataframe_to_user(name="Sorted Listings by Cash Flow", dataframe=df)

    return render_template("investment_templates/aparna_listings.html", listings=listings_data)