from datetime import datetime, UTC


def make_default_time() -> datetime:
    return datetime.now(UTC)
