#!/usr/bin/env python3
"""
Script để khởi động server FastAPI
Giải quyết vấn đề import conflicts
"""
import sys
import os
import uvicorn

# Thêm đường dẫn hiện tại vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def main() -> None:
    """Chạy server FastAPI.

    - PORT: port chạy server (default 8000)
    - RELOAD: 1 để bật reload (dev), mặc định tắt
    """
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "0") == "1"

    from app.main import app

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[current_dir] if reload else None,
    )

if __name__ == "__main__":
    main()