#!/usr/bin/env python3
"""
Qwen 模型部署验证脚本
检查容器状态、服务可用性、模型下载状态等
"""

import subprocess
import sys
import json
import time
from typing import Tuple, Optional

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("请运行: pip install requests")
    sys.exit(1)

# 颜色定义
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.NC}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.NC}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.NC}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.NC}")

def run_command(cmd: list, capture_output: bool = True) -> Tuple[int, str, str]:
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_container_status() -> bool:
    """检查容器状态"""
    print("1. 检查容器状态... ", end="", flush=True)
    code, stdout, _ = run_command(["docker", "compose", "ps", "ollama"])
    if code == 0 and "Up" in stdout and "healthy" in stdout:
        print_success("通过")
        return True
    else:
        print_error("失败")
        print_info("   容器未运行或未健康")
        return False

def check_service_port() -> bool:
    """检查服务端口是否可访问"""
    print("2. 检查服务端口 (11434)... ", end="", flush=True)
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_success("通过")
            return True
        else:
            print_error("失败")
            print_info(f"   HTTP 状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error("失败")
        print_info(f"   无法连接到 Ollama API: {e}")
        return False

def check_model_downloaded() -> Tuple[bool, Optional[str]]:
    """检查模型是否已下载"""
    print("3. 检查模型是否已下载... ", end="", flush=True)
    code, stdout, _ = run_command(["docker", "compose", "exec", "-T", "ollama", "ollama", "list"])
    if code == 0 and "qwen2.5:7b" in stdout:
        # 尝试提取模型大小
        lines = stdout.strip().split('\n')
        for line in lines:
            if "qwen2.5:7b" in line:
                parts = line.split()
                if len(parts) >= 3:
                    model_size = parts[2]
                    print_success(f"通过 (大小: {model_size})")
                    return True, model_size
        print_success("通过")
        return True, None
    else:
        print_error("失败")
        print_info("   未找到 qwen2.5:7b 模型")
        return False, None

def check_gpu_support() -> bool:
    """检查 GPU 支持"""
    print("4. 检查 GPU 支持... ", end="", flush=True)
    code, stdout, _ = run_command(["docker", "compose", "exec", "-T", "ollama", "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    if code == 0 and stdout.strip():
        gpu_name = stdout.strip().split('\n')[0]
        print_success(f"通过 (GPU: {gpu_name})")
        return True
    else:
        print_warning("警告 (未检测到 GPU，将使用 CPU)")
        return True  # 仍然算通过，只是使用 CPU

def test_model_response() -> bool:
    """测试模型响应"""
    print("5. 测试模型响应... ", end="", flush=True)
    try:
        payload = {
            "model": "qwen2.5:7b",
            "prompt": "你好",
            "stream": False
        }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                model_response = data["response"][:50]
                print_success("通过")
                if model_response:
                    print_info(f"   模型响应示例: {model_response}...")
                return True
            else:
                print_error("失败")
                print_info("   响应中未包含 'response' 字段")
                return False
        else:
            print_error("失败")
            print_info(f"   HTTP 状态码: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_error("失败")
        print_info("   请求超时（模型可能正在加载）")
        return False
    except requests.exceptions.RequestException as e:
        print_error("失败")
        print_info(f"   请求错误: {e}")
        return False

def check_data_volume() -> bool:
    """检查数据卷"""
    print("6. 检查数据卷... ", end="", flush=True)
    code, stdout, _ = run_command(["docker", "volume", "inspect", "second-brain_ollama_data"])
    if code == 0:
        try:
            volume_info = json.loads(stdout)
            if volume_info and len(volume_info) > 0:
                mountpoint = volume_info[0].get("Mountpoint", "未知")
                print_success("通过")
                print_info(f"   卷路径: {mountpoint}")
                return True
        except json.JSONDecodeError:
            pass
    print_error("失败")
    return False

def main():
    """主函数"""
    print("=" * 50)
    print("  检查 Qwen 模型部署状态")
    print("=" * 50)
    print()
    
    checks_passed = 0
    checks_failed = 0
    
    # 执行各项检查
    if check_container_status():
        checks_passed += 1
    else:
        checks_failed += 1
    
    if check_service_port():
        checks_passed += 1
    else:
        checks_failed += 1
    
    model_ok, _ = check_model_downloaded()
    if model_ok:
        checks_passed += 1
    else:
        checks_failed += 1
    
    if check_gpu_support():
        checks_passed += 1
    else:
        checks_failed += 1
    
    if test_model_response():
        checks_passed += 1
    else:
        checks_failed += 1
    
    if check_data_volume():
        checks_passed += 1
    else:
        checks_failed += 1
    
    # 汇总结果
    print()
    print("=" * 50)
    print("  检查结果汇总")
    print("=" * 50)
    print(f"通过: {Colors.GREEN}{checks_passed}{Colors.NC}")
    print(f"失败: {Colors.RED}{checks_failed}{Colors.NC}")
    print()
    
    if checks_failed == 0:
        print_success("所有检查通过！Qwen 模型已成功部署。")
        return 0
    else:
        print_error("部分检查失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

