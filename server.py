#!/usr/bin/env python3
"""
FFmpeg MCP Server - 强制盘符根目录映射版 v1.2.0

⚠️ 核心强制规则（已固化到代码）:
---------------------------------------
basedir 必须使用盘符根目录 (D:/, E:/, C:/)
任何子目录会被自动规范化为盘符根目录并发出警告！

解决的问题:
- 官方 {{basedir}}:{{basedir}} 在 Windows 上不工作
- 子目录映射导致容器内路径无法识别
- 实战证明：只有盘符根目录映射才可靠稳定

实战经验 sha256:b98d601b439325dd0216074d1d3c8b94e382889368a27eb70a1a2fdad15a5785
"""

import subprocess
import json
import sys
import re

def send_response(response):
    """发送 MCP 响应"""
    print(json.dumps(response), flush=True)

def send_error(id, code, message):
    """发送错误响应"""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message}
    })

def send_result(id, result):
    """发送成功响应"""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    })

def convert_windows_path(basedir: str) -> tuple:
    """
    将 Windows 路径转换为 Docker 兼容格式
    
    ⚠️ 强制规则（已固化到代码）：
    ------------------------------------
    basedir 应该是盘符根目录（如 D:/, E:/）
    任何子目录都会被自动规范化为盘符根目录！
    
    实战经验证明这是唯一可靠的路径映射方式：
    - ✅ basedir = "D:/"          -> volume: D:/:/work
    - ✅ basedir = "D:/subfolder" -> 自动修正为 D:/, volume: D:/:/work (带警告)
    - ✅ basedir = "E:/"          -> volume: E:/:/work
    
    为什么强制使用盘符根目录？
    1. Docker 的卷映射在 Windows 上必须映射整个盘符
    2. 子目录映射在 Linux 容器内无法正确识别 Windows 路径格式
    3. 实战测试：D:/subfolder 作为 basedir 会导致 "No such file or directory"
    
    Returns:
        tuple: (docker_volume_mount, normalized_basedir)
    """
    basedir = basedir.replace("\\", "/").rstrip('/')
    
    # 检测 Windows 路径 (如 D:/tecx/text 或 C:/Users/...)
    match = re.match(r'^([A-Za-z]:)/?(.*)', basedir)
    if match:
        drive = match.group(1)  # D:
        subpath = match.group(2)  # 可能的子路径，例如 "tecx/text"
        
        # ⚠️ 强制规范化：始终使用盘符根目录
        if subpath:
            print(f"⚠️ 警告: basedir 应该使用盘符根目录！", file=sys.stderr)
            print(f"   输入: {basedir}", file=sys.stderr)
            print(f"   自动修正为: {drive}/", file=sys.stderr)
            print(f"   建议: 请在调用时直接使用 '{drive}/' 作为 basedir", file=sys.stderr)
        
        # 映射整个盘符到 /work（强制规则）
        volume_mount = f"{drive}/:/work"
        normalized_basedir = f"{drive}/"
        
        return volume_mount, normalized_basedir
    else:
        # Linux/Mac 路径 -> 官方模式 (basedir:basedir)
        return f"{basedir}:{basedir}", basedir

def convert_any_windows_path(arg: str) -> str:
    """
    自动转换任意 Windows 路径为容器路径
    
    转换规则:
        D:/any/path/file.mp4 -> /work/any/path/file.mp4
        C:/Users/test.jpg -> /work/Users/test.jpg
    
    这样用户可以直接使用 Windows 路径，无需手动转换！
    """
    arg = arg.replace("\\", "/")
    
    # 检测 Windows 路径格式 (如 D:/xxx 或 C:/xxx)
    match = re.match(r'^([A-Za-z]):/(.*)', arg)
    if match:
        # drive = match.group(1)  # D: (盘符信息保留用于 volume mount)
        subpath = match.group(2)  # any/path/file.mp4
        return f"/work/{subpath}" if subpath else "/work"
    
    return arg


def run_ffmpeg(args: list, basedir: str) -> dict:
    """
    运行 FFmpeg 命令
    
    官方参数:
        args: FFmpeg 参数列表
        basedir: 基础目录 (如 D:/tecx/text)
    
    路径自动转换 (固化规则):
        1. basedir: D:/xxx -> volume mount: D:/:/work
        2. args 中的任意 Windows 路径自动转换:
           - D:/tecx/text/input.mp4 -> /work/tecx/text/input.mp4
           - D:/other/file.mp4 -> /work/other/file.mp4
        
    用户可以直接使用 Windows 路径，无需手动使用 /work/ 前缀！
    """
    volume_mount, _ = convert_windows_path(basedir)
    
    processed_args = [convert_any_windows_path(arg) for arg in args]
    
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", volume_mount,
        "zuozuoliang999/ffmpeg:7.1-cli"
    ] + processed_args
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "command": " ".join(docker_cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Command timeout (5 minutes)",
            "command": " ".join(docker_cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "command": " ".join(docker_cmd)
        }

def run_imagemagick(args: str, basedir: str) -> dict:
    """
    运行 ImageMagick 命令
    
    官方参数:
        args: ImageMagick 参数字符串
    
    路径自动转换 (固化规则):
        自动检测并转换所有 Windows 路径，用户无需手动使用 /work/ 前缀
    """
    volume_mount, _ = convert_windows_path(basedir) if basedir else ("", "")
    
    processed_args = re.sub(
        r'([A-Za-z]):/([^\s"\']+)',
        lambda m: f"/work/{m.group(2)}",
        args.replace("\\", "/")
    )
    
    docker_cmd = [
        "docker", "run", "--rm",
        "--entrypoint", "magick",
    ]
    
    if volume_mount:
        docker_cmd.extend(["-v", volume_mount])
    
    docker_cmd.append("zuozuoliang999/imagemagick:latest")
    docker_cmd.extend(processed_args.split())
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 合并 stdout 和 stderr（ImageMagick 有时输出到 stderr）
        combined_output = result.stdout + result.stderr
        return {
            "success": result.returncode == 0,
            "output": combined_output.strip() if combined_output else "(no output)",
            "command": " ".join(docker_cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "command": " ".join(docker_cmd)
        }

def file_exists(path: str, basedir: str = "") -> dict:
    """
    检查文件是否存在
    
    官方参数:
        path: 文件路径
    
    路径自动转换 (固化规则):
        D:/any/path/file.mp4 -> /work/any/path/file.mp4
    """
    volume_mount, _ = convert_windows_path(basedir) if basedir else ("", "")
    
    check_path = convert_any_windows_path(path)
    
    docker_cmd = ["docker", "run", "--rm"]
    
    if volume_mount:
        docker_cmd.extend(["-v", volume_mount])
    
    docker_cmd.extend([
        "zuozuoliang999/busybox:latest",
        "test", "-f", check_path
    ])
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "exists": result.returncode == 0,
            "path": path,
            "container_path": check_path,
            "command": " ".join(docker_cmd)
        }
    except Exception as e:
        return {
            "exists": False,
            "path": path,
            "error": str(e),
            "command": " ".join(docker_cmd)
        }

# 工具定义 - Windows 兼容版（重命名避免与 mcp-docker 冲突）
# ⚠️ 强制规则（已固化到代码）: basedir 必须使用盘符根目录 (D:/, E:/)
# 任何子目录会被自动规范化为盘符根目录！
TOOLS = [
    {
        "name": "ffmpeg-win",
        "description": "Run FFmpeg command with AUTO Windows path conversion. Paths like D:/path/file.mp4 are automatically converted to /work/path/file.mp4. ⚠️ IMPORTANT: basedir MUST be drive root (D:/, E:/), NOT subdirectory. Subdirectories are auto-corrected with warning.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "arguments to pass to ffmpeg. Windows paths (D:/xxx) are auto-converted to container paths (/work/xxx)"
                },
                "basedir": {
                    "type": "string",
                    "description": "⚠️ MUST BE DRIVE ROOT: D:/, E:/, C:/ etc. Do NOT use subdirectories! Example: Use 'D:/' not 'D:/videos'"
                }
            },
            "required": ["basedir", "args"]
        }
    },
    {
        "name": "imagemagick-win",
        "description": "Run ImageMagick command with AUTO Windows path conversion. Paths like D:/path/file.jpg are automatically converted. ⚠️ IMPORTANT: basedir MUST be drive root (D:/, E:/), NOT subdirectory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": "The arguments to pass to imagemagick. Windows paths are auto-converted"
                },
                "basedir": {
                    "type": "string",
                    "description": "⚠️ MUST BE DRIVE ROOT: D:/, E:/, C:/ etc. Do NOT use subdirectories! Will be auto-extracted from args if not provided."
                }
            },
            "required": ["args"]
        }
    },
    {
        "name": "file-exists-win",
        "description": "Check if a file exists with AUTO Windows path conversion. ⚠️ IMPORTANT: Drive letter is auto-extracted and forced to root (D:/, E:/).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full file path (e.g. D:/jianji_FFMPEG/video.mp4). Drive root (D:/) is auto-extracted and normalized."
                }
            },
            "required": ["path"]
        }
    }
]

def handle_request(request: dict):
    """处理 MCP 请求"""
    method = request.get("method")
    id = request.get("id")
    params = request.get("params", {})
    
    if method == "initialize":
        send_result(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "ffmpeg-mcp",
                "version": "1.2.0-force-drive-root"
            }
        })
    
    elif method == "tools/list":
        send_result(id, {"tools": TOOLS})
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "ffmpeg-win":
            basedir = arguments.get("basedir", "")
            args = arguments.get("args", [])
            result = run_ffmpeg(args, basedir)
            send_result(id, {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]})
        
        elif tool_name == "imagemagick-win":
            args = arguments.get("args", "")
            # 优先使用显式传入的 basedir，否则从 args 中提取盘符根目录
            basedir = arguments.get("basedir", "")
            if not basedir:
                # 从 args 中提取 Windows 路径并强制使用盘符根目录
                match = re.search(r'([A-Za-z]):[/\\]', args)
                if match:
                    basedir = f"{match.group(1)}:/"
            result = run_imagemagick(args, basedir)
            send_result(id, {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]})
        
        elif tool_name == "file-exists-win":
            path = arguments.get("path", "")
            # 从 path 中提取盘符并强制使用根目录
            basedir = ""
            match = re.search(r'([A-Za-z]):[/\\]', path)
            if match:
                basedir = f"{match.group(1)}:/"
            result = file_exists(path, basedir)
            send_result(id, {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]})
        
        else:
            send_error(id, -32601, f"Unknown tool: {tool_name}")
    
    elif method == "notifications/initialized":
        pass
    
    else:
        send_error(id, -32601, f"Method not found: {method}")

def main():
    """主循环"""
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            handle_request(request)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
