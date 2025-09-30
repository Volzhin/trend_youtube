from datetime import datetime
import isodate

def iso_duration_to_seconds(iso_str: str) -> int:
    try:
        return int(isodate.parse_duration(iso_str).total_seconds())
    except Exception:
        return 0

def today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")
