#!/usr/bin/env python
"""
一键启动后端 FastAPI 服务 和 Gradio 前端
"""

import subprocess
import sys
import time
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent

    # 后端命令：uvicorn app.main:app --host 0.0.0.0 --port 8000
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    # 前端命令：通过 app.gradio_ui 启动
    gradio_cmd = [
        sys.executable,
        "-m",
        "app.gradio_ui",
    ]

    backend_proc = None
    gradio_proc = None

    try:
        print("🚀 启动 FastAPI 后端服务 (http://localhost:8000)...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=project_root,
        )

        # 等后端先起来一点
        time.sleep(2)

        print("🎨 启动 Gradio 前端 (http://localhost:7860)...")
        gradio_proc = subprocess.Popen(
            gradio_cmd,
            cwd=project_root,
        )

        print("\n✅ 后端和前端已启动，按 Ctrl+C 退出。")

        # 等待两个子进程（任意一个退出就结束）
        while True:
            backend_code = backend_proc.poll()
            gradio_code = gradio_proc.poll()

            if backend_code is not None:
                print(f"\n⚠️ 后端进程退出，退出码: {backend_code}")
                break
            if gradio_code is not None:
                print(f"\n⚠️ 前端进程退出，退出码: {gradio_code}")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⏹ 收到 Ctrl+C，正在关闭子进程...")
    finally:
        # 优雅关闭子进程
        for name, proc in [("后端", backend_proc), ("前端", gradio_proc)]:
            if proc is not None and proc.poll() is None:
                print(f"  - 终止{name}进程 ...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"  - {name}进程未响应，强制杀死")
                    proc.kill()

        print("✅ 已退出。")

if __name__ == "__main__":
    main()