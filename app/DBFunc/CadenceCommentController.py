# controllers/CommentController.py
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import os
import re
import uuid

from app.extensions import db


# ----------------------- helpers -----------------------

def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace(",", "").replace("$", "").replace("%", "")
        try:
            return float(s)
        except Exception:
            return None
    return None

def _pick_dir(curr: Any,
              prev: Any,
              min_delta: Optional[float] = None,
              min_pct: Optional[float] = None,
              none_is: str = "neutral") -> str:
    c = _to_float(curr)
    p = _to_float(prev)
    if c is None or p is None:
        return none_is
    diff = c - p
    if diff == 0:
        return "neutral"
    if (min_delta is not None) or (min_pct is not None):
        significant = False
        if (min_delta is not None) and (abs(diff) >= min_delta):
            significant = True
        if (min_pct is not None) and (p != 0):
            pct_change = abs(diff) / abs(p) * 100.0
            if pct_change >= min_pct:
                significant = True
        if not significant:
            return "neutral"
    return "up" if diff > 0 else "down"

def _verdict(kind: str, dir_: str) -> str:
    if kind == "rates":
        return ("rates are likely to go up" if dir_ == "up"
                else "rates are likely to stay the same" if dir_ == "neutral"
                else "rates are likely to drop")
    if kind == "speed":
        return ("listings are likely to stay on market longer" if dir_ == "up"
                else "listings are likely to stay on market for about the same length" if dir_ == "neutral"
                else "listings are likely to stay on market shorter")
    if kind == "competition":
        return ("market is likely to be more competitive" if dir_ == "up"
                else "market is likely to be about as competitive" if dir_ == "neutral"
                else "market is likely to be less competitive")
    if kind == "price":
        return ("prices are likely to rise" if dir_ == "up"
                else "prices are likely to stay about the same" if dir_ == "neutral"
                else "prices are likely to fall")
    return ""

def _fmt_price(v: Any) -> str:
    try:
        fv = _to_float(v)
        return f"${int(fv):,}" if fv is not None else "?"
    except Exception:
        return "?" if v is None else str(v)

def _parse_ai_explainer(text: str) -> Dict[str, Any]:
    """
    Expect format:
      Title: ...
      Explanation: ...
      Advice:
      - ...
      - ...
      CTA: ...
    Return {title, explanation, advice(list), cta}
    """
    out: Dict[str, Any] = {"title": "", "explanation": "", "advice": [], "cta": ""}
    if not text:
        return out
    try:
        m = re.search(r"(?im)^\s*Title:\s*(.+)$", text)
        if m: out["title"] = m.group(1).strip()

        m = re.search(r"(?im)^\s*Explanation:\s*(.+)$", text)
        if m: out["explanation"] = m.group(1).strip()

        m = re.search(r"(?is)^\s*Advice:\s*(.+?)(?:^\s*CTA:|\Z)", text, re.MULTILINE)
        if m:
            adv = []
            for line in m.group(1).splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("-") or line.startswith("•") or re.match(r"^\d+[).]\s+", line):
                    clean = re.sub(r"^[-•]\s*|\d+[).]\s*", "", line).strip()
                    if clean:
                        adv.append(clean)
            out["advice"] = adv[:3]

        m = re.search(r"(?im)^\s*CTA:\s*(.+)$", text)
        if m: out["cta"] = m.group(1).strip()
    except Exception:
        pass
    return out


def _two_window_price_dir(self, stats: Dict[str, Any], k: int = 4, min_pct: float = 0.3) -> str:
    """
    Fallback: last k weeks vs prior k weeks % change on median_price_16w.
    min_pct in percent (e.g., 0.3 = 0.3%)
    """
    series = stats.get("median_price_16w") or []
    vals = [pt.get("median_price") for pt in series]
    vals = [v for v in vals if isinstance(v, (int, float)) and v is not None]
    if len(vals) < 2 * k:
        return "unknown"
    recent = sum(vals[-k:]) / k
    prior = sum(vals[-2 * k : -k]) / k
    if prior == 0:
        return "unknown"
    pct = (recent - prior) / abs(prior) * 100.0
    if abs(pct) < min_pct:
        return "same"
    return "up" if pct > 0 else "down"


# ----------------------- model -----------------------

class CadenceComment(db.Model):
    """
    NEW SHAPE: one row per cadence tying INPUT (digest) and OUTPUT (AI + send).
    """
    __tablename__ = "CadenceComment"

    id = db.Column(db.String(36), primary_key=True)  # uuid4
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), index=True, nullable=False)

    # when the cadence snapshot was taken
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # INPUT
    input_digest = db.Column(db.Text, nullable=False)  # JSON (metrics including dirs/conclusions/series)

    # OUTPUT
    ai_json = db.Column(db.Text)   # JSON {title, explanation, advice, cta}
    ai_text = db.Column(db.Text)   # raw text (optional)

    subject = db.Column(db.String(255))
    recipient = db.Column(db.String(255))
    test = db.Column(db.Boolean, nullable=False, default=False)
    send_status = db.Column(db.String(16))  # 'queued'|'generated'|'sent'|'fail'|'skipped'
    sent_at = db.Column(db.DateTime)

    note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_cadence_customer_time", "customer_id", "occurred_at"),
    )

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())


# ----------------------- controller -----------------------

class CommentController:
    """Store/load cadenced comments with input (digest) + output (AI/send) on the SAME row."""

    # ---- lifecycle: start -> save_ai -> mark_send ----

    def start_cadence(self, customer_id: int, metrics: Dict[str, Any],
                      when: Optional[datetime] = None) -> str:
        """
        Create a cadence row with INPUT digest (we also ensure dirs/conclusions are present).
        Returns cadence_id (uuid4).
        """

        cadence_id = CadenceComment.new_id()
        row = CadenceComment(
            id=cadence_id,
            customer_id=customer_id,
            occurred_at=when or datetime.utcnow(),
            input_digest=json.dumps(metrics, separators=(",", ":")),
            send_status="queued",
        )
        db.session.add(row)
        db.session.commit()
        return cadence_id

    def create_cadence_after_ai(self, customer_id: int, stats: dict,
                                ai_dict: dict, ai_text: str = None,
                                when: datetime = None, subject :str = None) -> str:
        """
        Create a CadenceComment row ONLY after we have a successful AI result.
        """
        cadence_id = CadenceComment.new_id()
        row = CadenceComment(
            id=cadence_id,
            customer_id=customer_id,
            occurred_at=when or datetime.utcnow(),
            input_digest=json.dumps({"stats": stats}, separators=(",", ":")),
            ai_json=json.dumps(ai_dict, separators=(",", ":")),
            ai_text=ai_text,
            send_status="generated",  # we have AI content but haven't sent yet
            sent_at=when or datetime.utcnow(),
            subject=subject
        )
        db.session.add(row)
        db.session.commit()
        return cadence_id

    def save_ai(self, cadence_id: str, ai_dict: Dict[str, Any], ai_text: Optional[str] = None) -> None:
        """
        Attach AI output (structured + optional raw) to the cadence row.
        """
        row = CadenceComment.query.get(cadence_id)
        if not row:
            return
        row.ai_json = json.dumps(ai_dict or {}, separators=(",", ":"))
        if ai_text:
            row.ai_text = ai_text
        # update stage unless already marked as sent/fail
        if not row.send_status or row.send_status in ("queued", "generated"):
            row.send_status = "generated"
        db.session.commit()

    def mark_send(self, cadence_id: str, subject: str, recipient: str,
                  test: bool, ok: bool, when: Optional[datetime] = None) -> None:
        """
        Finalize the cadence row with email send outcome.
        """
        row = CadenceComment.query.get(cadence_id)
        if not row:
            return
        row.subject = subject
        row.recipient = recipient
        row.test = bool(test)
        row.send_status = "sent" if ok else "fail"
        row.sent_at = when or datetime.utcnow()
        db.session.commit()

    # ---- readers ----

    def recent_cadences(self, customer_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Newest-first decoded cadences for rendering/admin.
        """
        rows = (CadenceComment.query
                .filter_by(customer_id=customer_id)
                .order_by(CadenceComment.occurred_at.desc())
                .limit(limit).all())
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append({
                "id": r.id,
                "occurred_at": r.occurred_at,
                "input_digest": json.loads(r.input_digest or "{}"),
                "ai": json.loads(r.ai_json) if r.ai_json else None,
                "ai_text": r.ai_text,
                "subject": r.subject,
                "recipient": r.recipient,
                "test": r.test,
                "send_status": r.send_status,
                "sent_at": r.sent_at,
                "note": r.note,
            })
        return out

    def recent_cadence_prompt_builder(self, out):
        prompt=''
        for r in out:
            prompt+=(
                f"Sent on {r['sent_at']} + \n"
                f" {r['ai_text']}\n"
            )
        return prompt


    def last_digest(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Convenience: return most recent INPUT digest (for trend arrows).
        """
        row = (CadenceComment.query
               .filter_by(customer_id=customer_id)
               .order_by(CadenceComment.occurred_at.desc())
               .first())
        if not row:
            return None
        try:
            return json.loads(row.input_digest or "{}")
        except Exception:
            return None


    # ---- AI generation (no implicit DB writes unless cadence_id passed) ----

    def generate_ai_explainer(self, customer: Any, segment: int,
                              current_metrics: Dict[str, Any],
                              cadence_id: Optional[str] = None) -> str:
        """
        Returns raw text in Title/Explanation/Advice/CTA format.
        If cadence_id is provided, stores raw text in that row (ai_text).
        """
        prompt = self.build_ai_explainer_prompt(customer, segment, current_metrics)
        text_out: Optional[str] = None

        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_apiKey")
            if api_key:
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=500,
                )
                text_out = (resp.choices[0].message.content or "").strip()
        except Exception:
            text_out = None

        if not text_out:
            name = getattr(customer, "name", "there")
            text_out = (
                "Title: This week’s quick read\n"
                f"Explanation: Hi {name}, rates look steady and homes are moving at a moderate pace. "
                "Competition clusters around well-priced listings.\n"
                "Advice:\n- Shortlist 3 homes under your top budget\n"
                "- Be tour-ready for new listings\n"
                "- Compare buydown vs. seller credit\n"
                "CTA: Reply 'meet' to set up a 15-min planning call."
            )

        if cadence_id:
            # store raw text to the same row
            row = CadenceComment.query.get(cadence_id)
            if row:
                row.ai_text = text_out
                if not row.send_status or row.send_status == "queued":
                    row.send_status = "generated"
                db.session.commit()

        return text_out


    def _normalize_dir_token(self, val: Any) -> str:
        if not isinstance(val, str):
            return "unknown"
        v = val.strip().lower()
        if v in ("up", "down", "same", "neutral"):  # treat neutral as same
            return "same" if v == "neutral" else v
        return "unknown"

    def _parse_ai_structured(self, text: str, segment: int) -> Dict[str, Any]:
        """
        Try to parse strict JSON; if it fails, try to yank the first {...} block.
        """

        def _safe_load(s: str) -> Optional[Dict[str, Any]]:
            try:
                return json.loads(s)
            except Exception:
                return None

        obj = _safe_load(text)
        if not obj:
            # crude extraction of first JSON object
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                obj = _safe_load(m.group(0))
        if not obj:
            return {}

        # normalize shape
        out = {
            "title": (obj.get("title") or "").strip(),
            "explanation": (obj.get("explanation") or "").strip(),
            "advice": list(obj.get("advice") or [])[:3],
            "cta": (obj.get("cta") or "").strip(),
            "conclusions": {
                "rates": self._normalize_dir_token(obj.get("conclusions", {}).get("rates")),
                "speed": self._normalize_dir_token(obj.get("conclusions", {}).get("speed")),
                "competition": self._normalize_dir_token(obj.get("conclusions", {}).get("competition")),
                "sold_price": self._normalize_dir_token(obj.get("conclusions", {}).get("sold_price")),
                "inventory": self._normalize_dir_token(obj.get("conclusions", {}).get("inventory")),
            },
        }
        return out

    def generate_ai_explainer_structured_from_stats(
            self,
            customer: Any,
            segment: int,
            stats: Dict[str, Any],
            metrics: Dict[str, Any],
            cadence_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Single call: build prompt from STATS only, get JSON, parse, add minimal fallback.
        If cadence_id is given, persist the AI JSON on that same row.
        """
        prompt = self.build_ai_explainer_prompt_from_stats(customer, segment, metrics)

        text_out: Optional[str] = None
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_apiKey")
            if api_key:
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500,
                )
                text_out = (resp.choices[0].message.content or "").strip()
        except Exception:
            text_out = None

        if not text_out:
            # Minimal offline fallback
            out = {
                "title": "Market snapshot",
                "explanation": "Here’s a quick read on speed, competition, and prices based on recent sales.",
                "advice": [
                    "Shortlist 2–3 options and plan a tour window",
                    "Discuss payment scenarios with your lender",
                    "Watch new listings that price fairly",
                ],
                "cta": "Reply 'meet' to schedule a 15-minute planning call with Wayber.",
            }
            if segment in (1, 2):  # buyers
                out["conclusions"] = {
                    "rates": "unknown",
                    "speed": "unknown",
                    "competition": "unknown",
                    "sold_price": "unknown",
                }
            elif segment == 3:  # seller
                out["conclusions"] = {
                    "sold_price": "unknown",
                    "speed": "unknown",
                    "inventory": "unknown",
                }
            else:
                # default to buyer schema
                out["conclusions"] = {
                    "rates": "unknown",
                    "speed": "unknown",
                    "competition": "unknown",
                    "sold_price": "unknown",
                }

        else:
            out = self._parse_ai_structured(text_out, segment)

        # Persist on the same cadence row if requested


        try:
            self.create_cadence_after_ai(customer.id,
                                         stats,
                                         metrics,
                                         text_out,
                                         datetime.now(),
                                         out['title'])
        except Exception:
            pass

        return out

    def build_ai_explainer_prompt_from_stats(self, customer, segment: int, metrics) -> str:
        """
        Build an LLM prompt from stats, switching the 'conclusions' targets
        depending on buyer/seller segment.

        Buyer (1/2):    conclusions = rates | speed | competition | sold_price
        Seller (3):     conclusions = sold_price | speed | inventory
        """
        seg_map = {1: "Non-Active Buyer", 2: "Active Buyer", 3: "Seller"}
        seg_name = seg_map.get(int(segment or 1), "Non-Active Buyer")
        is_seller = (int(segment or 1) == 3)

        # Pull a few recent cadences (AI titles/explanations) to give context
        recent = self.recent_cadences(customer.id, limit=5)
        history = self.recent_cadence_prompt_builder(recent) if hasattr(self, "recent_cadence_prompt_builder") else ""

        # Common header
        header = (
            "You are a real-estate advisor for Wayber (WA).\n"
            "Use ONLY the data block provided. Do not invent numbers. Be concise and clear.\n\n"
            f"CUSTOMER:\n- Name: {getattr(customer, 'name', 'there')}\n"
            f"- Segment: {seg_name} (1=Non-Active Buyer, 2=Active Buyer, 3=Seller)\n"
            f"- City: {getattr(getattr(customer, 'maincity', None), 'City', 'N/A')}\n\n"
            "DATA:\n"
            f"{metrics}\n\n"
            "HISTORY:\n"
            f"{history}\n\n"
            "TASK:\n"
        )

        if not is_seller:
            # BUYER conclusions
            task = (
                "1) Decide directional conclusions (one word each) for:\n"
                "   - rates: up|down|same|unknown\n"
                "   - speed (DOM — larger means slower): up|down|same|unknown\n"
                "   - competition (use sale_to_list_avg_pct, pct_over_ask, price_cuts): up|down|same|unknown\n"
                "   - price (use PRICE_SERIES_16W trend): up|down|same|unknown\n"
                "2) Write a short title (≤60 chars), a 90–120 word explanation, and 3 short advice bullets.\n"
                "3) Provide a CTA line (encourage booking a planning call with Wayber).\n"
                "4) Don't say “As a non active buyer…”. Speak directly and briefly.\n\n"
                "OUTPUT: Return ONLY valid JSON (no backticks, no prose):\n"
                "{\n"
                '  "title": "string",\n'
                '  "explanation": "string",\n'
                '  "advice": ["string","string","string"],\n'
                '  "cta": "string",\n'
                '  "conclusions": {\n'
                '    "rates": "up|down|same|unknown",\n'
                '    "speed": "up|down|same|unknown",\n'
                '    "competition": "up|down|same|unknown",\n'
                '    "sold_price": "up|down|same|unknown"\n'
                "  }\n"
                "}\n"
                'Rules: If a dimension is missing in DATA, set it to "unknown". Keep it brief and useful.\n'
            )
        else:
            # SELLER conclusions
            # Tell the model exactly which fields to use, and preferred fallbacks.
            task = (
                "1) Decide directional conclusions (one word each) for the SELLER view:\n"
                "   - sold_price: up|down|same|unknown  (use median_sold_price if present, else avg_sold_price)\n"
                "   - speed:      up|down|same|unknown  (use median_days; note: higher DOM ⇒ slower ⇒ 'up')\n"
                "   - inventory:  up|down|same|unknown  (use active_listings if present; else use new_listings as a proxy)\n"
                "2) Write a short title (≤60 chars), a 90–120 word explanation, and 3 short advice bullets tailored to a seller.\n"
                "3) Provide a CTA line (encourage booking a planning call with Wayber).\n"
                "4) Be concrete. Do not invent numbers not in DATA. Do not use boilerplate.\n\n"
                "OUTPUT: Return ONLY valid JSON (no backticks, no prose):\n"
                "{\n"
                '  "title": "string",\n'
                '  "explanation": "string",\n'
                '  "advice": ["string","string","string"],\n'
                '  "cta": "string",\n'
                '  "conclusions": {\n'
                '    "sold_price": "up|down|same|unknown",\n'
                '    "speed": "up|down|same|unknown",\n'
                '    "inventory": "up|down|same|unknown"\n'
                "  }\n"
                "}\n"
                'Rules: If a dimension is missing in DATA, set it to "unknown". Keep it brief and useful.\n'
            )

        return header + task


commentcontroller = CommentController()
