from typing import Optional, Union
from typing import Tuple, Optional


NumberLike = Union[float, int, str]

def _to_float(x: Optional[NumberLike]) -> Optional[float]:
    """Coerce numbers like '6.6%', '$725,000' to float; None → None."""
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



def _dir_abs(curr, prev, abs_thr):
    if curr is None or prev is None:
        return "neutral"
    diff = curr - prev
    if diff > abs_thr:  return "up"
    if diff < -abs_thr: return "down"
    return "neutral"

def _fmt_money(v):
    if v is None:
        return "-"
    try:
        return f"${int(round(v)):,}"
    except Exception:
        return str(v)

def badge_label_and_color(sale_to_list, pct_over_ask):
    if sale_to_list is None:
        return "BALANCED", "#9ca3af"
    if sale_to_list >= 100.5 or pct_over_ask >= 45:
        return "HOT", "#e67e22"      # orange
    if sale_to_list <= 99.5 and pct_over_ask <= 30:
        return "COOL", "#3498db"     # blue
    return "BALANCED", "#27ae60"     # green

from typing import Optional, List, Dict, Any
from datetime import datetime

def _most_recent_week_start(stats):
    series = (stats or {}).get("median_price_16w") or []
    if not series:
        return datetime.utcnow().date()
    # series is oldest→newest
    last = series[-1].get("week_start")
    try:
        return datetime.fromisoformat(last).date()
    except Exception:
        return datetime.utcnow().date()

def _label_color(label):
    return {
        "HOT": "#e74c3c",        # red
        "BALANCED": "#6366f1",   # indigo/blue
        "COOL": "#27ae60",       # green
    }.get(label, "#9ca3af")

def derive_header_fields(stats, ai=None):
    # prefer AI competition signal if you have it
    ai_dir = (((ai or {}).get("conclusions") or {}).get("competition") or "").lower()
    if ai_dir == "up":
        label = "HOT"
    elif ai_dir == "down":
        label = "COOL"
    elif ai_dir in ("same", "neutral"):
        label = "BALANCED"
    else:
        label = label_from_stats(stats)  # fallback to stats

    as_of_date = _most_recent_week_start(stats)
    return {
        "label": label,
        "badge_bg": _label_color(label),
        "as_of": nice_ord_date(as_of_date.strftime("%Y-%m-%d")),  # or "%b %d, %Y"
    }

def nice_ord_date(value):
    # Accept either a datetime or an ISO/date string like '2025-10-20'
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)  # handles 'YYYY-MM-DD' and full ISO
        except ValueError:
            dt = datetime.strptime(value, "%Y-%m-%d")  # fallback
    else:
        dt = value

    d = dt.day
    suffix = 'th' if 10 <= d % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')
    return f"{dt.strftime('%b')} {d}{suffix} {dt:%Y}"


def label_from_stats(stats):
    sl = stats.get("sale_to_list_avg_pct") or 0.0
    cuts = stats.get("pct_price_cuts") or 0.0
    # simple thresholds; tweak to taste
    if sl >= 101.0 or cuts < 5:      # lots over ask / few cuts
        return "HOT"
    if sl <= 99.5 or cuts >= 25:     # discounts / many cuts
        return "COOL"
    return "BALANCED"

def verbalize_stats(stats: Dict[str, Any], emailcadence) -> str:
    """
    Turn raw StatsModelRun(...) dict into a compact, readable block for the LLM.
    Does not compute directions; just reports the numbers.
    """
    s = stats or {}
    # basic lines (guard against None)
    def _v(k, fmt="{:,}"):
        v = s.get(k)
        if v is None:
            return "N/A"
        try:
            return fmt.format(v)
        except Exception:
            return str(v)

    lines = []
    lines.append(f"Below is the data for the latest {emailcadence} days")
    lines.append(f"DOM_MEDIAN_IN={_v('median_days')}, DOM_AVG={_v('avg_days_on_market')}, FASTEST_DAYS={_v('fastest_days')}")
    lines.append(f"OVER_ASK_PCT={_v('pct_over_ask','{:.1f}')}, UNDER_7D_PCT={_v('pct_under_7d','{:.1f}')}, PRICE_CUTS_PCT={_v('pct_price_cuts','{:.1f}')}")
    # lines.append(f"SALE_TO_LIST_AVG_PCT={_v('sale_to_list_avg_pct','{:.2f}')}")
    # lines.append(f"SOLD_PRICE_AVG={_v('avg_sold_price','$ {:,}')}, SOLD_PRICE_MEDIAN={_v('median_sold_price','$ {:,}')}")

    lines.append(f"Below is the data for the last 16 weeks days")
    # 16-week series (oldest→newest). Keep it machine-friendly and human-readable.
    series = s.get("median_price_16w") or []
    ser_pairs = []
    for pt in series:
        ws = pt.get("week_start", "N/A")
        mp = pt.get("median_price")
        cnt = pt.get("count", 0)
        mp_str = "null" if mp is None else str(int(mp))
        ser_pairs.append(f"({ws},{mp_str},n={cnt})")
    if ser_pairs:
        lines.append("PRICE_SERIES_16W=" + ", ".join(ser_pairs))
    else:
        lines.append("PRICE_SERIES_16W=(none)")

    series = s.get("pending_16w") or []
    ser_pairs = []
    for pt in series:
        ws = pt.get("week_start", "N/A")
        cnt = pt.get("new_pending", 0)
        ser_pairs.append(f"({ws},listingpending={cnt})")
    if ser_pairs:
        lines.append("PENDING_COUNT_16W=" + ", ".join(ser_pairs))
    else:
        lines.append("PENDING_COUNT_16W=(none)")


    # NEW: 16-week active listings series (new actives per week; oldest→newest)
    series_active = s.get("newlistings_16w") or []
    act_pairs = []
    for pt in series_active:
        ws = pt.get("week_start", "N/A")
        na = pt.get("newlistings", 0)
        act_pairs.append(f"({ws},{int(na)})")
    if act_pairs:
        lines.append("NEW_LISTINGS_16W=" + ", ".join(act_pairs))
    else:
        lines.append("NEW_LISTINGS_16W=(none)")

    series_active = s.get("active_listing_16W") or []
    act_pairs = []
    for pt in series_active:
        ws = pt.get("week_start", "N/A")
        na = pt.get("active_count", 0)
        act_pairs.append(f"({ws},{int(na)})")
    if act_pairs:
        lines.append("ACTIVE_LISTINGS_16W=" + ", ".join(act_pairs))
    else:
        lines.append("ACTIVE_LISTINGS_16W=(none)")

    # One compact blob
    return "\n".join(lines)


def _normalize_dir_token_py(val):
    v = (str(val or "")).strip().lower()
    if v in ("up", "down", "same", "neutral"):
        return "same" if v == "neutral" else v
    return "unknown"

def verdict_sentence(kind, dir_token):
    d = _normalize_dir_token_py(dir_token)
    if kind == "rates":
        if d == "up":    return "Rates are likely to go up"
        if d == "down":  return "Rates are likely to drop"
        if d == "same":  return "Rates are likely to stay the same"
        return "rate direction is unclear"
    if kind == "speed":
        if d == "up":    return "Listings are likely to stay on market longer"
        if d == "down":  return "Listings are likely to stay on market shorter"
        if d == "same":  return "Listings are likely to stay on market for about the same length"
        return "time-on-market direction is unclear"
    if kind == "competition":
        if d == "up":    return "Market is likely to be more seller friendly"
        if d == "down":  return "Market is likely to be more buyer friendly"
        if d == "same":  return "Competitiveness of listings to remain about the same"
        return "competition direction is unclear"
    if kind == "sold_price":
        if d == "up":    return "Prices are likely to rise"
        if d == "down":  return "Prices are likely to fall"
        if d == "same":  return "Prices are likely to stay about the same"
        return "price direction is unclear"
    return ""