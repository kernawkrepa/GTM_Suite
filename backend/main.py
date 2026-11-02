import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

import backend.log_store as log_store
from backend.db.database import engine, SessionLocal
from backend.db.models import Base
from backend.routers import clips, discovery, logs, queue, settings, streamers

logger = logging.getLogger(__name__)


def _run_migrations(conn):
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if "streamers" in tables:
        cols = {c["name"] for c in inspector.get_columns("streamers")}
        for col, ddl in [
            ("partnership_date", "VARCHAR"),
            ("followers_count", "INTEGER DEFAULT 0"),
            ("last_live_at", "DATETIME"),
            ("approval_source", "VARCHAR"),
            ("approval_notes", "TEXT"),
            ("approval_file_path", "VARCHAR"),
        ]:
            if col not in cols:
                conn.execute(text(f"ALTER TABLE streamers ADD COLUMN {col} {ddl}"))

    if "clips" in tables:
        cols = {c["name"] for c in inspector.get_columns("clips")}
        for col, ddl in [
            ("creator_name", "VARCHAR"),
            ("is_outro", "BOOLEAN DEFAULT 0"),
            ("rating", "INTEGER DEFAULT 0"),
            ("cached_at", "DATETIME"),
        ]:
            if col not in cols:
                conn.execute(text(f"ALTER TABLE clips ADD COLUMN {col} {ddl}"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log_store.setup(logging.getLogger())

    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)
        _run_migrations(conn)

    # clear stale download jobs from previous run
    db = SessionLocal()
    try:
        from backend.db.models import DownloadJob
        db.query(DownloadJob).delete()
        db.commit()
    finally:
        db.close()

    logger.info("GTM Suite backend started")
    yield
    logger.info("GTM Suite backend shutting down")


app = FastAPI(title="GTM Suite", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streamers.router)
app.include_router(clips.router)
app.include_router(queue.router)
app.include_router(settings.router)
app.include_router(discovery.router)
app.include_router(logs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
