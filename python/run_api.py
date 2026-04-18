import os
import sys

# Ensure the repo root is on sys.path so `from python.server.api import app`
# resolves correctly regardless of the working directory the caller uses.
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import uvicorn
from python.server.api import app

if __name__ == "__main__":
    host = "0.0.0.0" if os.getenv("DOCKER_CONTAINER") == "true" else "127.0.0.1"
    uvicorn.run(app, host=host, port=18000, log_level="info")
