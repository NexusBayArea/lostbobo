from app.core.fake_job_store import FakeJobStore
from app.core.job_store_interface import JobStoreInterface

_store = None


def get_job_store() -> JobStoreInterface:
    global _store
    if _store is None:
        _store = FakeJobStore()
    return _store


def set_job_store(store: JobStoreInterface):
    global _store
    _store = store


def reset_job_store():
    global _store
    _store = None
