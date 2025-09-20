# controllers/CommentController.py
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from sqlalchemy import text
from app.extensions import db

class CadenceComment(db.Model):
    __tablename__ = "CadenceComment"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), index=True, nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False)     # not “weekly” – any cadence
    tag = db.Column(db.String(32), nullable=False)           # 'email_digest', 'ai_explainer', 'note'
    payload = db.Column(db.Text, nullable=False)             # text or JSON
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class CommentController:
    """MVP: store/load cadenced comments + build AI explainer prompt."""

    # --- raw add/get helpers ---
    def add_comment(self, customer_id: int, text_payload: str,
                    tag: str = "note", when: Optional[datetime] = None) -> None:
        when = when or datetime.utcnow()
        db.session.add(CadenceComment(customer_id=customer_id,
                                      occurred_at=when,
                                      tag=tag,
                                      payload=text_payload))
        db.session.commit()

    def add_email_digest(self, customer_id: int, metrics: Dict[str, Any],
                         when: Optional[datetime] = None) -> None:
        """Store a compact JSON digest from the email you just built/sent."""
        when = when or datetime.utcnow()
        compact = {
            "ts": when.strftime("%Y-%m-%d"),
            "rate": metrics.get("rate"),
            "dom": metrics.get("dom"),
            "sale_to_list": metrics.get("sale_to_list"),
            "pct_under_7d": metrics.get("pct_under_7d"),
            "pct_over_ask": metrics.get("pct_over_ask"),
            "pct_price_cuts": metrics.get("pct_price_cuts"),
            "label": metrics.get("label"),  # HOT/BALANCED/COOL if you set it
        }
        db.session.add(CadenceComment(customer_id=customer_id,
                                      occurred_at=when,
                                      tag="email_digest",
                                      payload=json.dumps(compact, separators=(",", ":"))))
        db.session.commit()

    def recent_email_digests(self, customer_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        rows = (CadenceComment.query
                .filter_by(customer_id=customer_id, tag="email_digest")
                .order_by(CadenceComment.occurred_at.desc())
                .limit(limit)
                .all())
        out = []
        for r in rows:
            try:
                out.append(json.loads(r.payload))
            except Exception:
                continue
        return out

    # --- AI prompt + (optional) call ---
    def build_ai_explainer_prompt(self, customer: Any, segment: int,
                                  current_metrics: Dict[str, Any],
                                  history_limit: int = 3) -> str:
        seg_map = {1: "Cold buyer", 2: "Hot buyer", 3: "Seller"}
        seg_name = seg_map.get(int(segment or 1), "Cold buyer")

        recents = self.recent_email_digests(customer.id, limit=history_limit)
        lines = []
        for r in recents[::-1]:  # oldest → newest
            lines.append(f"- {r.get('ts','?')}: rate {r.get('rate','?')}%, DOM {r.get('dom','?')}, "
                         f"sale→list {r.get('sale_to_list','?')}%, label {r.get('label','?')}")
        history_block = "\n".join(lines) if lines else "(no prior digests)"

        cm = current_metrics or {}
        curr_line = (f"Now: rate {cm.get('rate','?')}%, DOM {cm.get('dom','?')}, "
                     f"sale→list {cm.get('sale_to_list','?')}%, label {cm.get('label','?')}.")

        return f"""You are a real-estate advisor for Wayber (WA). Write a brief, plain-English explanation
for the customer below using the last few weekly snapshots PLUS the current one.

CUSTOMER
- Name: {getattr(customer, 'name', 'there')}
- Segment: {seg_name} (1=cold buyer, 2=hot buyer, 3=seller)
- City: {getattr(getattr(customer, 'maincity', None), 'City', 'N/A')}

HISTORY (old→new)
{history_block}

CURRENT SNAPSHOT
{curr_line}

WHAT TO PRODUCE (FINAL ANSWER ONLY, no analysis):
1) A short title (≤60 chars).
2) A concise explanation (≤120 words) connecting history → now and setting expectation.
3) Three bullets of advice tailored to this segment.
4) One CTA line.

TONE: clear, calm, helpful. Use only the numbers given.
FORMAT:
Title: ...
Explanation: ...
Advice:
- ...
- ...
- ...
CTA: ...
"""

    def generate_ai_explainer(self, customer: Any, segment: int,
                              current_metrics: Dict[str, Any],
                              save_comment: bool = True) -> str:
        prompt = self.build_ai_explainer_prompt(customer, segment, current_metrics)
        text_out = None
        # Optional: call OpenAI if configured (safe to skip)
        try:
            import os
            from openai import OpenAI
            api_key = os.getenv("OPENAI_apiKey")
            if api_key:
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=500,
                )
                text_out = resp.choices[0].message.content.strip()
        except Exception:
            text_out = None

        if not text_out:
            name = getattr(customer, "name", "there")
            text_out = (
                f"Title: This week’s quick read\n"
                f"Explanation: Hi {name}, rates are steady and homes are moving at a moderate pace. "
                f"Competition clusters around well-priced homes.\n"
                f"Advice:\n- Shortlist 3 homes under top budget\n- Plan a same-day tour window\n"
                f"- Consider buydown or seller credit scenarios\n"
                f"CTA: Reply 'sheet' for a payment breakdown or 'tour' to see homes."
            )

        if save_comment:
            self.add_comment(customer.id, text_out, tag="ai_explainer")

        return text_out

commentcontroller = CommentController()
