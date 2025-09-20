from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

Base = declarative_base()
from app.extensions import db


class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)

    # Buyer preferences
    minprice = db.Column(db.Integer, nullable=True)
    idealprice = db.Column(db.Integer, nullable=True)
    maxprice = db.Column(db.Integer, nullable=True)
    idealsqft = db.Column(db.Integer, nullable=True)
    minsqft = db.Column(db.Integer, nullable=True)
    maxsqft = db.Column(db.Integer, nullable=True)
    lot_size = db.Column(db.Integer, nullable=True)
    parkingspaceneeded = db.Column(db.Integer, nullable=True)

    # Status / associations
    active = db.Column(db.Boolean, nullable=True)
    customer_type_id = db.Column(db.Integer, db.ForeignKey('CustomerType.id'))
    maincity_id = db.Column(db.Integer, db.ForeignKey('WashingtonCities.city_id'))

    # Email preferences
    dontemail = db.Column(db.Boolean, nullable=True)  # renamed from opted_out

    # Cadence fields (UTC timestamps recommended)
    email_cadence_days = db.Column(db.SmallInteger, nullable=False, default=14)
    paused = db.Column(db.Boolean, nullable=False, default=False)
    last_email_sent_at = db.Column(db.DateTime)
    next_email_due_at = db.Column(db.DateTime)  # UTC

    # Last time we interacted (not necessarily an email)
    last_contacted = db.Column(db.DateTime, default=datetime.utcnow)

    # Example relationship, if defined elsewhere in your models:
    # customerzpid_array = db.relationship('CustomerZone', back_populates='customer')

    def __str__(self):
        return (
            f"Customer(ID: {self.id}, Name: {self.name} {self.lastname}, Email: {self.email}, "
            f"Phone: {self.phone}, Price Range: {self.minprice}-{self.maxprice} (Ideal: {self.idealprice}), "
            f"Square Footage: {self.minsqft}-{self.maxsqft} (Ideal: {self.idealsqft}))"
        )

class WeeklyComment(db.Model):
    __tablename__ = "WeeklyComment"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), index=True, nullable=False)
    week_start = db.Column(db.Date, nullable=False)  # Monday of the ISO week
    tag = db.Column(db.String(32))                  # e.g., 'email','note','tour','seller'
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("idx_wc_customer_week", "customer_id", "week_start"),
    )

def _monday_of(dt: datetime) -> date:
    d = dt.date()
    return d - timedelta(days=d.weekday())  # Monday=0

class CustomerController:
    """
    All database operations for Customer live here.
    Routes should call into this controller (no db.session in route files).
    """

    # ---------- Basic CRUD / Queries ----------

    def getAllCustomer(self) -> List[Customer]:
        return Customer.query.all()

    def getCustomerByID(self, id: int) -> Optional[Customer]:
        return Customer.query.get(id)

    def getCustomerByEmail(self, email: str) -> Optional[Customer]:
        return Customer.query.filter_by(email=email).first()

    def getCustomerByIDType(self, id: int, as_dict: bool = False):
        customers = Customer.query.filter_by(customer_type_id=id).all()

        if as_dict:
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "lastname": c.lastname,
                    "email": c.email,
                    "phone": c.phone,
                    "price_range": f"{c.minprice}-{c.maxprice} (Ideal: {c.idealprice})",
                    "square_footage": f"{c.minsqft}-{c.maxsqft} (Ideal: {c.idealsqft})",
                    "last_contacted": c.last_contacted.strftime("%Y-%m-%d %H:%M:%S") if c.last_contacted else None,
                }
                for c in customers
            ]

        return customers

    def getCustomerZpidInterests(self):
        """Returns customers with their zpid interests eager-loaded (relationship must exist)."""
        return Customer.query.options(joinedload(Customer.customerzpid_array)).all()

    def get_active_customers(self, as_dict: bool = False):
        customers = Customer.query.filter_by(active=True).all()

        if as_dict:
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "lastname": c.lastname,
                    "email": c.email,
                    "phone": c.phone,
                    "price_range": f"{c.minprice}-{c.maxprice} (Ideal: {c.idealprice})",
                    "square_footage": f"{c.minsqft}-{c.maxsqft} (Ideal: {c.idealsqft})",
                    "last_contacted": c.last_contacted.strftime("%Y-%m-%d %H:%M:%S") if c.last_contacted else None,
                }
                for c in customers
            ]

        return customers

    # ---------- Cadence: Selection, Recording, Bulk Ops ----------

    def get_due_customers(self, now_utc: Optional[datetime] = None, limit: int = 500) -> List[Customer]:
        """
        Return customers who are due for an email right now (per-customer cadence).
        Conditions:
         - dontemail is False/0
         - paused is False/0
         - next_email_due_at <= now_utc
        """
        now_utc = now_utc or datetime.utcnow()
        return (
            Customer.query
            .filter(
                Customer.dontemail.is_(False),
                Customer.paused.is_(False),
                Customer.next_email_due_at.isnot(None),
                Customer.next_email_due_at <= now_utc,
            )
            .order_by(Customer.next_email_due_at.asc())
            .limit(limit)
            .all()
        )

    def shouldsendEmail(self, customer) -> bool:
        """
        True if it's time to email this customer again, based on
        datetime.now(), customer.email_cadence_days, and last_email_sent_at.
        """
        cadence = int(customer.email_cadence_days or 0)
        if cadence <= 0:
            return True
        last = customer.last_email_sent_at
        if not last:
            return True
        return (datetime.now() - last) >= timedelta(days=cadence)

    def update_last_email_sent_at(self, customer):
        customer.last_email_sent_at = datetime.utcnow()
        cadence = int(customer.email_cadence_days or 14)
        customer.next_email_due_at = customer.last_email_sent_at + timedelta(days=cadence)
        customer.last_contacted = customer.last_email_sent_at
        db.session.commit()

    def record_send_success(self, customer: Customer, when_utc: Optional[datetime] = None) -> None:
        """Mark a successful send and advance next due by cadence days."""
        when_utc = when_utc or datetime.utcnow()
        cadence = int(customer.email_cadence_days or 14)
        customer.last_email_sent_at = when_utc
        customer.next_email_due_at = when_utc + timedelta(days=cadence)

    def record_send_failure(self, customer: Customer, when_utc: Optional[datetime] = None, backoff_days: int = 1) -> None:
        """On failure, set a short backoff so we don't retry immediately."""
        when_utc = when_utc or datetime.utcnow()
        customer.next_email_due_at = when_utc + timedelta(days=backoff_days)

    def initialize_missing_schedules(self, when_utc: Optional[datetime] = None) -> int:
        """
        Give a next_email_due_at to customers that are missing one.
        Returns number of rows affected.
        """
        when_utc = when_utc or datetime.utcnow()
        result = db.session.execute(
            text("""
                UPDATE Customer
                SET next_email_due_at = DATE_ADD(:now_utc, INTERVAL email_cadence_days DAY)
                WHERE next_email_due_at IS NULL
                  AND COALESCE(dontemail, 0) = 0
                  AND COALESCE(paused, 0) = 0
            """),
            {"now_utc": when_utc},
        )
        db.session.commit()
        return result.rowcount or 0

    def advance_all_due_now_sql(self, when_utc: Optional[datetime] = None) -> int:
        """
        Pure-SQL advancement for everyone who is due at the moment this runs.
        Returns number of rows affected.
        """
        when_utc = when_utc or datetime.utcnow()
        result = db.session.execute(
            text("""
                UPDATE Customer
                SET last_email_sent_at = :now_utc,
                    next_email_due_at  = DATE_ADD(:now_utc, INTERVAL email_cadence_days DAY)
                WHERE COALESCE(dontemail, 0) = 0
                  AND COALESCE(paused, 0) = 0
                  AND next_email_due_at IS NOT NULL
                  AND next_email_due_at <= :now_utc
            """),
            {"now_utc": when_utc},
        )
        db.session.commit()
        return result.rowcount or 0

    def set_cadence(
        self,
        customer_id: int,
        email_cadence_days: Optional[int] = None,
        paused: Optional[bool] = None,
        dontemail: Optional[bool] = None,
        next_email_due_at: Optional[datetime] = None,
    ) -> None:
        """
        Update cadence-related fields for a customer.
        Only parameters passed (non-None) are applied.
        """
        c = Customer.query.get_or_404(customer_id)
        if email_cadence_days is not None:
            c.email_cadence_days = int(email_cadence_days)
        if paused is not None:
            c.paused = bool(paused)
        if dontemail is not None:
            c.dontemail = bool(dontemail)
        if next_email_due_at is not None:
            c.next_email_due_at = next_email_due_at
        db.session.commit()

    # ---------- Serialization Helpers ----------

    def to_email_payload(self, c: Customer) -> Dict[str, Any]:
        """
        Shape a Customer into the dict expected by your email sender
        (e.g., EmailOutToLeads). Adjust/extend fields as your templates need.
        """
        payload = {
            "id": str(c.id),
            "email": c.email or "",
            "name": c.name or "",
            "lastname": c.lastname or "",
            "phone": c.phone or "",
            "last_contacted": c.last_contacted.strftime("%Y-%m-%d %H:%M:%S") if c.last_contacted else "",
            # Optional marketing fields built from numeric prefs:
            "price_range": f"{c.minprice}-{c.maxprice} (Ideal: {c.idealprice})",
            "square_footage": f"{c.minsqft}-{c.maxsqft} (Ideal: {c.idealsqft})",
        }
        # You can also include last email time if your template uses it:
        if c.last_email_sent_at:
            payload["last_email_sent_at"] = c.last_email_sent_at.strftime("%Y-%m-%d %H:%M:%S")
        return payload

    def preview_due_as_dict(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return a small list of due customers as dicts for quick visibility."""
        now_utc = datetime.utcnow()
        rows = self.get_due_customers(now_utc=now_utc, limit=limit)
        return [
            {
                "id": c.id,
                "email": c.email,
                "cadence_days": c.email_cadence_days,
                "last_email_sent_at": c.last_email_sent_at.isoformat() if c.last_email_sent_at else None,
                "next_email_due_at": c.next_email_due_at.isoformat() if c.next_email_due_at else None,
            }
            for c in rows
        ]

    # ---------- Transaction Control ----------

    def commit(self) -> None:
        db.session.commit()

    def rollback(self) -> None:
        db.session.rollback()

    def add_comment(self, customer_id: int, comment: str, tag: str = "email", when: Optional[datetime] = None) -> None:
        when = when or datetime.utcnow()
        rec = WeeklyComment(
            customer_id=customer_id,
            week_start=_monday_of(when),
            tag=tag,
            comment=comment,
            created_at=when
        )
        db.session.add(rec)
        db.session.commit()

    def last_comments(self, customer_id: int, limit: int = 3) -> List[Dict]:
        rows = (WeeklyComment.query
                .filter_by(customer_id=customer_id)
                .order_by(WeeklyComment.created_at.desc())
                .limit(limit)
                .all())
        return [
            {"when": r.created_at.strftime("%Y-%m-%d"), "tag": r.tag, "text": r.comment}
            for r in rows
        ]
# Module-level singleton for easy import in routes
customercontroller = CustomerController()
