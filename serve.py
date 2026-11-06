"""Waitress WSGI launcher for local deployment of LoongBBS Next.

用法：
    .venv\\Scripts\\python.exe serve.py

可用环境变量覆盖监听地址：
    LOONG_BBS_HOST      默认 127.0.0.1（改成 0.0.0.0 可让局域网访问）
    LOONG_BBS_PORT      默认 5000
    LOONG_BBS_THREADS   默认 8
"""
from __future__ import annotations

import os

from waitress import serve

from run import app

HOST = os.environ.get("LOONG_BBS_HOST", "127.0.0.1")
PORT = int(os.environ.get("LOONG_BBS_PORT", "5000"))
THREADS = int(os.environ.get("LOONG_BBS_THREADS", "8"))

if __name__ == "__main__":
    print(f"LoongBBS Next listening on http://{HOST}:{PORT}", flush=True)
    serve(app, host=HOST, port=PORT, threads=THREADS, ident="LoongBBS")
