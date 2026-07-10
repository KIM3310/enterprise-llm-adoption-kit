"""Entry point for running the backend with ``python -m app``."""

import os

import uvicorn

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("APP_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST,
        port=int(os.getenv("APP_PORT", str(DEFAULT_PORT))),
        reload=False,
    )
