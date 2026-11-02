import logging
from collections import deque
from threading import Lock

_store: deque = deque(maxlen=1000)
_lock = Lock()


class _StoreHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        with _lock:
            _store.append({
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "time": record.created,
            })


def setup(logger: logging.Logger) -> None:
    handler = _StoreHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)


def get_logs() -> list[dict]:
    with _lock:
        return list(_store)


def clear_logs() -> None:
    with _lock:
        _store.clear()
