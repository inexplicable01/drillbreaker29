from typing import Tuple, Optional
from datetime import datetime
import random
import os

def get_current_rates(test: bool = False) -> Tuple[Optional[float], Optional[float]]:
    """
    Dummy rate source.
    Returns (30yr_fixed, 5/6_ARM) as floats.
    - If test=True, returns fixed values for predictable tests.
    - Otherwise, uses a day-stable pseudo-random drift around a base.
    You can override via env: RATE30_OVERRIDE, ARM56_OVERRIDE.
    """
    # Env overrides (useful for manual testing)
    r30_override = os.getenv("RATE30_OVERRIDE")
    arm_override = os.getenv("ARM56_OVERRIDE")
    if r30_override or arm_override:
        r30 = float(r30_override) if r30_override else 6.60
        arm = float(arm_override) if arm_override else max(r30 - 0.70, 0.0)
        return round(r30, 2), round(arm, 2)

    if test:
        return 6.60, 5.90

    # Day-stable drift so previews change a bit each day but are reproducible
    seed = int(datetime.utcnow().strftime("%Y%m%d"))
    rng = random.Random(seed)

    base_30 = 6.60
    drift_30 = rng.uniform(-0.10, 0.10)  # ±10 bps
    r30 = base_30 + drift_30

    # ARM usually lower than 30yr fixed
    base_spread = 0.70
    drift_spread = rng.uniform(-0.05, 0.05)  # ±5 bps on spread
    arm = max(r30 - (base_spread + drift_spread), 0.0)

    return round(r30, 2), round(arm, 2)
