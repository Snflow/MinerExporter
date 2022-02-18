from datetime import datetime

def remove_prefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix):]
    return s

def remove_suffix(s, suffix):
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s

def get_path(s):
    return list(filter(None, s.split(".")))

def get_value(obj, path):
    if not path:
        return obj
    current = obj
    for field in path:
        if isinstance(current, dict):
            if field not in current:
                return float("NaN")
            current = current[field]
        elif isinstance(current, list):
            if not field.isnumeric():
                return float("NaN")
            i = int(field)
            if i >= len(current):
                return float("NaN")
            current = current[i]
        else:
            return float("NaN")
    return current

def timestamp_to_now(timestamp):
    d = datetime.fromtimestamp(timestamp)
    diff = datetime.now() - d
    return diff.total_seconds()
    #days = diff.days
    #hours, rest = divmod(diff.seconds, 3600)
    #minutes, seconds = divmod(rest, 60)
    #return (days, hours, minutes, seconds)

def minutes_to_interval(total_minutes):
    return total_minutes * 60.0
