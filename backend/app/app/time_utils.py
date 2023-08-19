from datetime import datetime

import pytz


def timestamp_within_today(timestamp: int, timezone: str) -> bool:
    """Check if a timestamp is within today."""
    tz = pytz.timezone(timezone)
    now = datetime.now(tz=tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return today_start.timestamp() <= timestamp <= today_end.timestamp()
