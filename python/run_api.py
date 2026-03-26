import uvicorn
from server.api import app

if __name__ == "__main__":
    # Use 0.0.0.0 for Docker containers, 127.0.0.1 for local development
    host = "0.0.0.0" if __import__("os").getenv("DOCKER_CONTAINER") == "true" else "127.0.0.1"
    uvicorn.run(app, host=host, port=18000, log_level="info")
