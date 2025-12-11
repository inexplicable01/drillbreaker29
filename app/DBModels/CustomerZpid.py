from dataclasses import dataclass, field, InitVar, fields
from typing import Optional, Dict, List
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, DateTime, Numeric, JSON
Base = declarative_base()
from app.extensions import db
from datetime import datetime

class CustomerZpid(db.Model):
    __tablename__ = 'CustomerZpid'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id', ondelete="CASCADE"))
    zpid = db.Column(db.BigInteger, db.ForeignKey('BriefListing.zpid', ondelete="CASCADE"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    is_retired = db.Column(db.Boolean, default=False)

    # Change tracking fields
    last_price = db.Column(db.BigInteger, nullable=True)
    last_home_status = db.Column(db.String(100), nullable=True)
    last_zestimate = db.Column(db.BigInteger, nullable=True)
    last_days_on_zillow = db.Column(db.Integer, nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    last_changed_at = db.Column(db.DateTime, nullable=True)
    last_alerted_at = db.Column(db.DateTime, nullable=True)
    change_history = db.Column(db.JSON, nullable=True)

    def __init__(self, customer_id, zpid, created_at, is_retired=False):
        self.customer_id = customer_id
        self.zpid = zpid
        self.created_at = created_at
        self.is_retired = is_retired

    def __repr__(self):
        return f"<CustomerZpid id={self.id} customer_id={self.customer_id} zpid={self.zpid}>"

    def detect_changes(self, current_listing) -> Dict[str, any]:
        """
        Compare current listing to last known state and detect changes.

        Args:
            current_listing: BriefListing object with current state

        Returns:
            Dict with changes detected: {'has_changes': bool, 'changes': [list of change descriptions]}
        """
        changes = []

        # Check price change
        if current_listing.price != self.last_price:
            old_price = self.last_price or 0
            new_price = current_listing.price or 0
            if old_price > 0 and new_price > 0:
                diff = new_price - old_price
                pct = (diff / old_price) * 100
                if diff < 0:
                    changes.append(f"Price dropped ${abs(diff):,} ({abs(pct):.1f}%) from ${old_price:,} to ${new_price:,}")
                else:
                    changes.append(f"Price increased ${diff:,} ({pct:.1f}%) from ${old_price:,} to ${new_price:,}")
            elif new_price > 0:
                changes.append(f"Price set to ${new_price:,}")

        # Check status change
        if current_listing.homeStatus != self.last_home_status:
            changes.append(f"Status changed from {self.last_home_status} to {current_listing.homeStatus}")

        # Check zestimate change (only if significant)
        if current_listing.zestimate and self.last_zestimate:
            zest_diff = abs(current_listing.zestimate - self.last_zestimate)
            if zest_diff > 10000:  # Only report if changed by $10k+
                if current_listing.zestimate > self.last_zestimate:
                    changes.append(f"Zestimate increased by ${zest_diff:,}")
                else:
                    changes.append(f"Zestimate decreased by ${zest_diff:,}")

        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'old_state': {
                'price': self.last_price,
                'home_status': self.last_home_status,
                'zestimate': self.last_zestimate
            },
            'new_state': {
                'price': current_listing.price,
                'home_status': current_listing.homeStatus,
                'zestimate': current_listing.zestimate
            }
        }

    def update_snapshot(self, listing, changes_detected=None):
        """
        Update snapshot with current listing state.

        Args:
            listing: BriefListing object
            changes_detected: Optional list of change descriptions
        """
        self.last_price = listing.price
        self.last_home_status = listing.homeStatus
        self.last_days_on_zillow = listing.daysOnZillow
        self.last_zestimate = listing.zestimate
        self.last_checked_at = datetime.utcnow()

        if changes_detected:
            self.last_changed_at = datetime.utcnow()
            # Add to change history
            if not self.change_history:
                self.change_history = []
            self.change_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'changes': changes_detected
            })

    def mark_alerted(self):
        """Mark that we sent an alert for this listing."""
        self.last_alerted_at = datetime.utcnow()
