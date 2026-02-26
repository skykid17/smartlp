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

def wait_for_mongot(client, timeout=180):
    """Wait until mongot's search index API is reachable and the knowledge_base
    collection is accessible. This confirms mongot is up and synced with mongod
    well enough to accept createSearchIndexes commands.
    """
    start = time.time()
    db = client.smartlp

    while time.time() - start < timeout:
        try:
            if "knowledge_base" in db.list_collection_names():
                list(db.knowledge_base.list_search_indexes())
                print("mongot API ready.")
                return
        except Exception:
            pass
        time.sleep(2)

    raise RuntimeError(f"mongot not ready after {timeout}s")

def is_db_seeded(client):
    doc = client.smartlp.settings.find_one({"id": "global"})
    return doc and doc.get("db_seeded") is True

def restore_archive(client):
    result = subprocess.run(
        ["mongorestore", "--uri", URI, "--gzip", f"--archive={ARCHIVE_PATH}"],
    )
    if result.returncode != 0:
        # Verify the critical collection exists before treating this as fatal.
        count = client.smartlp.knowledge_base.count_documents({})
        if count == 0:
            raise RuntimeError(f"mongorestore failed (exit {result.returncode}) and knowledge_base is empty.")
        print(f"mongorestore exited {result.returncode} but knowledge_base has {count} docs — continuing.")
    client.smartlp.settings.update_one(
        {"id": "global"},
        {"$set": {"db_seeded": True}},
        upsert=True,
    )

def start_application():
    debug = os.getenv("APP_DEBUG", "True").lower() in ("true", "1", "yes")
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = os.getenv("APP_PORT", "8800")

    if debug:
        # Development: use Flask-SocketIO's built-in Werkzeug server
        os.execvp(sys.executable, [sys.executable, "app.py"])
    else:
        # Production: use Gunicorn with threading worker (required for Socket.IO)
        gunicorn_cmd = [
            "gunicorn",
            "--worker-class", "gthread",
            "--threads", "4",
            "-w", "1",
            "--bind", f"{host}:{port}",
            "wsgi:app",
        ]
        os.execvp("gunicorn", gunicorn_cmd)

def main():
    wait_for_mongo(URI)
    client = MongoClient(URI)
    if not is_db_seeded(client):
        restore_archive(client)
    wait_for_mongot(client)
    from src.services.rag import rag_service
    print("Setting up RAG service...")
    rag_service.init()
    start_application()


if __name__ == "__main__":
    main()