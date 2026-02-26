import subprocess
import time
import os
import sys
from pathlib import Path

from pymongo import MongoClient


def _bootstrap_sys_path() -> None:
    """Ensure imports work when running this file directly.

    Many modules in this repo import via the top-level namespace `services.*`.
    That requires `src/` to be on `sys.path`.
    """

    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"
    
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


_bootstrap_sys_path()

URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true")
ARCHIVE_PATH = os.getenv(
    "SMARTLP_ARCHIVE",
    str(Path(__file__).resolve().with_name("smartlp.archive")),
)

def wait_for_mongo(uri, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("MongoDB not reachable")

def wait_for_mongot(client, timeout=60):
    start = time.time()
    db = client.smartlp

    while time.time() - start < timeout:
        try:
            if "knowledge_base" in db.list_collection_names():
                list(db.knowledge_base.list_search_indexes())
                return
        except Exception:
            pass
        time.sleep(2)

    raise RuntimeError("mongot not ready")

def is_db_seeded(client):
    doc = client.smartlp.settings.find_one({"id": "global"})
    return doc and doc.get("db_seeded") is True

def restore_archive(client):
    subprocess.run(
        ["mongorestore", "--uri", URI, "--gzip", f"--archive={ARCHIVE_PATH}"],
        check=True,
    )
    client.smartlp.settings.update_one(
        {"id": "global"},
        {"$set": {"db_seeded": True}},
        upsert=True,
    )

def start_application():
    os.execvp(sys.executable, [sys.executable, "app.py"])

def main():
    wait_for_mongo(URI)
    client = MongoClient(URI)
    if not is_db_seeded(client):
        restore_archive(client)
    wait_for_mongot(client)
    from src.services.rag import rag_service

    rag_service.init()
    start_application()


if __name__ == "__main__":
    main()