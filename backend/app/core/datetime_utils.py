from datetime import datetime, timezone

def get_now_utc() -> datetime:
    """Returns current UTC datetime. Can be easily mocked in tests."""
    return datetime.now(timezone.utc)
