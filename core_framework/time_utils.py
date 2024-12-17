from datetime import datetime, timezone


def make_default_time() -> datetime:
    return datetime.now(timezone.utc)
