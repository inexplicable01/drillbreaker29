# rates_outlook.py  (pure-Python, no extra deps; Python 3.8)
from typing import Dict, List, Any, Optional

def _sma(x: List[float], k: int) -> Optional[float]:
    if not x or len(x) < k:
        return None
    return sum(x[-k:]) / float(k)

def _two_window_dir(x: List[float], k: int = 4, min_pct: float = 0.15) -> str:
    """
    Compare avg of last k vs prior k (weekly data).
    min_pct is percentage threshold (0.15 = 0.15% change) to call up/down.
    """
    if not x or len(x) < 2 * k:
        return "unknown"
    recent = sum(x[-k:]) / k
    prior  = sum(x[-2*k:-k]) / k
    if prior == 0:
        return "unknown"
    pct = (recent - prior) / abs(prior) * 100.0
    if abs(pct) < min_pct:
        return "same"
    return "up" if pct > 0 else "down"

def _per_week_slope(x: List[float], k: int = 4) -> float:
    """
    Naive slope: difference between last-k avg and prior-k avg, per week.
    """
    if not x or len(x) < 2 * k:
        return 0.0
    recent = sum(x[-k:]) / k
    prior  = sum(x[-2*k:-k]) / k
    return (recent - prior) / float(k)

def _last_or_none(x: List[float]) -> Optional[float]:
    return x[-1] if x else None

def _est_20y_from_15_30(y15: Optional[float], y30: Optional[float]) -> Optional[float]:
    """
    If you don’t have a clean 20Y series, approximate it between 15Y and 30Y.
    Linear blend tends to be reasonable in practice.
    """
    if y15 is None and y30 is None:
        return None
    if y15 is None:
        return y30  # fallback
    if y30 is None:
        return y15  # fallback
    return (y15 + y30) / 2.0

def mortgage_rate_outlook(
    history: Dict[str, List[float]],
    current: Optional[Dict[str, float]] = None,
    weeks_ahead: int = 4,
) -> Dict[str, Dict[str, Any]]:
    """
    Inputs
      history: dict of weekly rates (oldest->newest or newest-last; we only read newest-last)
               keys: '15y_fixed', '20y_fixed' (optional), '30y_fixed', '5_1_arm'
      current: optional override for current values (same keys)
      weeks_ahead: small horizon for a naive forecast

    Returns for each product:
      {
        "now": float or None,
        "direction": "up"|"down"|"same"|"unknown",
        "forecast_weeks": N,
        "forecast": float or None,
        "source": "history|approx"
      }
    """
    products = ["15y_fixed", "20y_fixed", "30y_fixed", "5_1_arm"]
    out: Dict[str, Dict[str, Any]] = {}

    # normalize ordering to "newest last" (if caller passed newest-first, this still works for SMA over tails)
    # (we assume lists are already in chronological order; no special handling needed)

    # prepare helpers for 20Y estimate if missing
    h15 = history.get("15y_fixed", []) or []
    h30 = history.get("30y_fixed", []) or []
    if not history.get("20y_fixed"):
        est_series = []
        # try to estimate each week if aligned lengths; otherwise just use last blend
        if len(h15) == len(h30) and h15 and h30:
            for a, b in zip(h15, h30):
                est_series.append(_est_20y_from_15_30(a, b))
        else:
            est_series = []
        history["20y_fixed"] = est_series

    for key in products:
        series = history.get(key, []) or []
        now = (current or {}).get(key)
        if now is None:
            now = _last_or_none(series)

        # Direction from two-window compare on the series
        direction = _two_window_dir(series, k=4, min_pct=0.15)

        # Simple per-week slope forecast
        slope = _per_week_slope(series, k=4)
        forecast = (now + slope * weeks_ahead) if (now is not None) else None

        src = "history"
        if key == "20y_fixed" and not series:
            # estimate from last 15y/30y if possible
            est_now = _est_20y_from_15_30(_last_or_none(h15), _last_or_none(h30))
            if now is None and est_now is not None:
                now = est_now
                forecast = now + ((_per_week_slope(h15, 4) + _per_week_slope(h30, 4)) / 2.0) * weeks_ahead
                direction = _two_window_dir((h15[-8:-4] + h30[-8:-4] + h15[-4:] + h30[-4:]) or [], 4, 0.15) or "same"
                src = "approx"

        out[key] = {
            "now": round(now, 3) if isinstance(now, (int, float)) else None,
            "direction": direction,
            "forecast_weeks": weeks_ahead,
            "forecast": round(forecast, 3) if isinstance(forecast, (int, float)) else None,
            "source": src,
        }

    return out
