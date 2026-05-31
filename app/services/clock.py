from datetime import datetime


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")
