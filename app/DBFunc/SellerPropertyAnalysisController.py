from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc
from app.extensions import db
from app.DBModels.SellerPropertyAnalysis import SellerPropertyAnalysis


class SellerPropertyAnalysisController:
    """
    Controller for managing SellerPropertyAnalysis database operations.
    Handles CRUD operations and analysis retrieval for Level 2 sellers.
    """

    def create_analysis(
        self,
        customer_id: int,
        seller_address: str,
        latitude: float = None,
        longitude: float = None,
        property_type: str = None,
        num_comps: int = None,
        comp_zpids: list = None,
        predicted_price: int = None,
        price_per_sqft: float = None,
        confidence_lower: int = None,
        confidence_upper: int = None,
        r_squared: float = None,
        median_comp_price: int = None,
        avg_comp_sqft: float = None,
        avg_days_on_market: int = None,
        median_price_per_sqft: float = None,
        model_features: dict = None,
        notes: str = None
    ) -> SellerPropertyAnalysis:
        """
        Create a new seller property analysis record.
        """
        analysis = SellerPropertyAnalysis(
            customer_id=customer_id,
            analysis_date=datetime.utcnow(),
            seller_address=seller_address,
            latitude=latitude,
            longitude=longitude,
            property_type=property_type,
            num_comps=num_comps,
            comp_zpids=comp_zpids,
            predicted_price=predicted_price,
            price_per_sqft=price_per_sqft,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            r_squared=r_squared,
            median_comp_price=median_comp_price,
            avg_comp_sqft=avg_comp_sqft,
            avg_days_on_market=avg_days_on_market,
            median_price_per_sqft=median_price_per_sqft,
            model_features=model_features,
            notes=notes
        )

        # Calculate week-over-week change
        previous_analysis = self.get_latest_analysis_for_customer(customer_id)
        if previous_analysis and predicted_price and previous_analysis.predicted_price:
            analysis.week_over_week_change_dollars = predicted_price - previous_analysis.predicted_price
            analysis.week_over_week_change_pct = (
                (predicted_price - previous_analysis.predicted_price) / previous_analysis.predicted_price * 100
            )

        db.session.add(analysis)
        db.session.commit()
        return analysis

    def get_analysis_by_id(self, analysis_id: int) -> Optional[SellerPropertyAnalysis]:
        """Get a specific analysis by ID"""
        return SellerPropertyAnalysis.query.get(analysis_id)

    def get_latest_analysis_for_customer(self, customer_id: int) -> Optional[SellerPropertyAnalysis]:
        """
        Get the most recent analysis for a given customer.
        """
        return (
            SellerPropertyAnalysis.query
            .filter_by(customer_id=customer_id)
            .order_by(desc(SellerPropertyAnalysis.analysis_date))
            .first()
        )

    def get_all_analyses_for_customer(
        self,
        customer_id: int,
        limit: int = None
    ) -> List[SellerPropertyAnalysis]:
        """
        Get all analyses for a customer, ordered by most recent first.
        """
        query = (
            SellerPropertyAnalysis.query
            .filter_by(customer_id=customer_id)
            .order_by(desc(SellerPropertyAnalysis.analysis_date))
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_analyses_in_date_range(
        self,
        customer_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[SellerPropertyAnalysis]:
        """
        Get all analyses for a customer within a date range.
        """
        return (
            SellerPropertyAnalysis.query
            .filter(
                SellerPropertyAnalysis.customer_id == customer_id,
                SellerPropertyAnalysis.analysis_date >= start_date,
                SellerPropertyAnalysis.analysis_date <= end_date
            )
            .order_by(SellerPropertyAnalysis.analysis_date.asc())
            .all()
        )

    def get_historical_trend(
        self,
        customer_id: int,
        weeks: int = 12
    ) -> List[SellerPropertyAnalysis]:
        """
        Get the last N weeks of analyses for trend visualization.
        """
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks)
        return self.get_analyses_in_date_range(
            customer_id=customer_id,
            start_date=cutoff_date,
            end_date=datetime.utcnow()
        )

    def should_run_analysis(self, customer_id: int, days_between_analyses: int = 7) -> bool:
        """
        Check if enough time has passed since the last analysis.
        Returns True if no previous analysis exists or if enough days have passed.
        """
        latest = self.get_latest_analysis_for_customer(customer_id)
        if not latest:
            return True

        days_since_last = (datetime.utcnow() - latest.analysis_date).days
        return days_since_last >= days_between_analyses

    def delete_analysis(self, analysis_id: int) -> bool:
        """Delete an analysis by ID. Returns True if successful."""
        analysis = self.get_analysis_by_id(analysis_id)
        if analysis:
            db.session.delete(analysis)
            db.session.commit()
            return True
        return False

    def get_summary_stats_for_customer(self, customer_id: int) -> dict:
        """
        Get summary statistics across all analyses for a customer.
        """
        analyses = self.get_all_analyses_for_customer(customer_id)

        if not analyses:
            return {
                'total_analyses': 0,
                'first_analysis_date': None,
                'latest_analysis_date': None,
                'latest_predicted_price': None,
                'avg_predicted_price': None,
                'price_range': None
            }

        prices = [a.predicted_price for a in analyses if a.predicted_price]

        return {
            'total_analyses': len(analyses),
            'first_analysis_date': analyses[-1].analysis_date if analyses else None,
            'latest_analysis_date': analyses[0].analysis_date if analyses else None,
            'latest_predicted_price': analyses[0].predicted_price if analyses else None,
            'avg_predicted_price': sum(prices) // len(prices) if prices else None,
            'price_range': {
                'min': min(prices) if prices else None,
                'max': max(prices) if prices else None
            }
        }


# Module-level singleton for easy import
sellerpropertyanalysiscontroller = SellerPropertyAnalysisController()