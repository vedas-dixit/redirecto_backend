from datetime import datetime, timezone
from models.models import URL


def get_ttl_and_status(expires_at: datetime | None) -> tuple[str, str]:
    if not expires_at:
        return "Never", "Active"

    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    ttl_days = (expires_at - now).days
    status = "Expired" if expires_at < now else "Active"
    return f"{ttl_days} days", status


def format_time_diff(ts: datetime) -> str:
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
        ts = ts.replace(tzinfo=timezone.utc)

    diff = now - ts
    minutes = int(diff.total_seconds() // 60)
    hours = minutes // 60

    return f"{minutes} mins ago" if hours == 0 else f"{hours} hours ago"
