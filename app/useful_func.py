def safe_float_conversion(value, default=0.0):
    try:
        return float(value)
    except ValueError:
        return default

def safe_int_conversion(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default

