from fastapi import APIRouter
import backend.log_store as log_store

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
def get_logs():
    return log_store.get_logs()


@router.delete("", status_code=204)
def clear_logs():
    log_store.clear_logs()
