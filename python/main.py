from pathlib import Path
import sys
import logging
import time
import threading

# Set up Python path to allow relative imports
PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from server.grpc_server import serve as serve_grpc
from server.api import app
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start both gRPC server (port 60051) and FastAPI server (port 8000)."""
    
    # Start gRPC in background thread
    logger.info("Starting Python gRPC server on 127.0.0.1:60051...")
    grpc_thread = threading.Thread(target=lambda: serve_grpc(host="127.0.0.1", port=60051), daemon=True)
    grpc_thread.start()
    
    # Wait a bit for gRPC to bind
    time.sleep(2)
    
    # Start FastAPI in foreground on 127.0.0.1:8000 (localhost only)
    logger.info("Starting Python FastAPI server on 127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()