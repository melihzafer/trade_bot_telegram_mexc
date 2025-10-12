"""
Time utilities - timezone handling and date/time helpers.
"""
from datetime import datetime, timezone
import pytz

from .config import TZ


def get_timezone():
    """Get configured timezone object."""
    try:
        return pytz.timezone(TZ)
    except pytz.UnknownTimeZoneError:
        return pytz.UTC


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def now_local() -> datetime:
    """Get current datetime in configured timezone."""
    tz = get_timezone()
    return datetime.now(tz)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC."""
    if dt.tzinfo is None:
        # Assume local timezone if naive
        tz = get_timezone()
        dt = tz.localize(dt)
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime) -> datetime:
    """Convert datetime to configured timezone."""
    tz = get_timezone()
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    return dt.strftime(fmt)
