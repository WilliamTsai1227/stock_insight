from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  

def get_time_range_by_period(period="day"):
    """
    period 可選值: day, week, month, quarter, halfyear, year
    """
    tz = ZoneInfo("Asia/Taipei")
    now = datetime.now(tz)

    if period == "day":
        start = datetime(now.year, now.month, now.day, tzinfo=tz)
        end = start + timedelta(days=1)

    elif period == "week":
        start = datetime(now.year, now.month, now.day, tzinfo=tz) - timedelta(days=now.weekday())
        end = start + timedelta(days=7)

    elif period == "month":
        start = datetime(now.year, now.month, 1, tzinfo=tz)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1, tzinfo=tz)
        else:
            end = datetime(now.year, now.month + 1, 1, tzinfo=tz)

    elif period == "quarter":
        quarter = (now.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start = datetime(now.year, start_month, 1, tzinfo=tz)
        if quarter == 4:
            end = datetime(now.year + 1, 1, 1, tzinfo=tz)
        else:
            end = datetime(now.year, start_month + 3, 1, tzinfo=tz)

    elif period == "halfyear":
        if now.month <= 6:
            start = datetime(now.year, 1, 1, tzinfo=tz)
            end = datetime(now.year, 7, 1, tzinfo=tz)
        else:
            start = datetime(now.year, 7, 1, tzinfo=tz)
            end = datetime(now.year + 1, 1, 1, tzinfo=tz)

    elif period == "year":
        start = datetime(now.year, 1, 1, tzinfo=tz)
        end = datetime(now.year + 1, 1, 1, tzinfo=tz)

    else:
        raise ValueError("Unsupported period type")

    return start, end    # Example：2025-06-01 00:00:00+08:00

