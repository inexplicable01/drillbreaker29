def safe_float_conversion(value, default=0.0):

    try:
        return float(value)
    except Exception:
        return default



def safe_int_conversion(value, default=0):
    try:
        return int(value)
    except Exception:
        return default

def print_and_log(message):
    log_file_path = 'logfile.txt'  # Specify your log file name here
    print(message)
    with open(log_file_path, 'a') as file:
        file.write(message + '\n')