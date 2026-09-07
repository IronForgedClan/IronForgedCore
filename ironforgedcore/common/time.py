from datetime import datetime

from dateutil.relativedelta import relativedelta


def render_relative_time(target: datetime) -> str:
    delta = relativedelta(datetime.now().astimezone(), target)

    if delta.years > 0:
        return f"{delta.years} year{'s' if delta.years > 1 else ''} ago"
    elif delta.months > 0:
        return f"{delta.months} month{'s' if delta.months > 1 else ''} ago"
    elif delta.days > 6:
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.hours > 0:
        return f"{delta.hours} hour{'s' if delta.hours > 1 else ''} ago"
    elif delta.minutes > 0:
        return f"{delta.minutes} minute{'s' if delta.minutes > 1 else ''} ago"
    else:
        return f"{delta.seconds} second{'s' if delta.seconds != 1 else ''} ago"


def format_duration_hours(hours: float | None, suffix: str | None = None) -> str:
    """Format a duration in days/hours/minutes as a compact string"""

    if hours is None:
        return "-"

    suffix = f" {suffix}" if suffix else ""

    total_minutes = hours * 60
    if total_minutes < 1:
        minutes = 1 if hours > 0 else 0
        return f"{minutes} min{suffix}"

    if total_minutes < 60:
        minutes = int(total_minutes)
        return f"{minutes} min{suffix}"

    total_hours_int = int(hours)
    minutes = int(round((hours - total_hours_int) * 60))
    if minutes == 60:
        total_hours_int += 1
        minutes = 0

    if total_hours_int < 24:
        if minutes == 0:
            return f"{total_hours_int} hr{suffix}"
        return f"{total_hours_int} hr {minutes} min{suffix}"

    days = total_hours_int // 24
    hours_remainder = total_hours_int % 24
    if minutes == 0 and hours_remainder == 0:
        return f"{days} d{suffix}"
    if minutes == 0:
        return f"{days} d {hours_remainder} hr{suffix}"
    return f"{days} d {hours_remainder} hr {minutes} min{suffix}"
