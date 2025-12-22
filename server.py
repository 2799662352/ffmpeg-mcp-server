#!/usr/bin/env python3
"""
FFmpeg MCP Server - 与官方 API 一致的优化版
解决 Windows 路径兼容性问题 (官方 {{basedir}}:{{basedir}} 在 Windows 上不工作)
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
    
    官方设计: volumes: ['{{basedir}}:{{basedir}}']
    问题: D:/tecx/text:D:/tecx/text 在 Linux 容器内无效
    
    优化方案: 映射整个盘符！
    - D:/tecx/text -> volumes: D:/:/work, 容器内: /work/tecx/text
    - 这样路径结构保持一致，更简单可靠
    
    Returns:
        tuple: (docker_volume_mount, container_path_prefix, original_subpath)
    """
    basedir = basedir.replace("\\", "/")
    
    # 检测 Windows 路径 (如 D:/tecx/text 或 C:/Users/...)
    match = re.match(r'^([A-Za-z]:)/?(.*)', basedir)
    if match:
        drive = match.group(1)  # D:
        subpath = match.group(2)  # tecx/text
        # 映射整个盘符到 /work
        volume_mount = f"{drive}/:/work"
        # 容器内完整路径
        container_path = f"/work/{subpath}" if subpath else "/work"
        return volume_mount, container_path.rstrip('/')
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
    volume_mount, container_prefix = convert_windows_path(basedir)
    original_basedir = basedir.replace("\\", "/")
    
    # 自动转换所有 Windows 路径为容器路径
    processed_args = []
    for arg in args:
        # 优先替换完整的 basedir 路径
        if original_basedir and original_basedir in arg:
            arg = arg.replace(original_basedir, container_prefix)
        else:
            # 自动检测并转换任意 Windows 路径
            arg = convert_any_windows_path(arg)
        processed_args.append(arg)
    
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
    volume_mount, container_prefix = convert_windows_path(basedir) if basedir else ("", "")
    original_basedir = basedir.replace("\\", "/") if basedir else ""
    
    # 处理参数中的路径 - 自动转换所有 Windows 路径
    processed_args = args
    if original_basedir and original_basedir in args:
        processed_args = args.replace(original_basedir, container_prefix)
    
    # 自动检测并转换剩余的 Windows 路径
    def replace_windows_paths(text: str) -> str:
        return re.sub(
            r'([A-Za-z]):/([^\s"\']+)',
            lambda m: f"/work/{m.group(2)}",
            text
        )
    processed_args = replace_windows_paths(processed_args)
    
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
    volume_mount, container_prefix = convert_windows_path(basedir) if basedir else ("", "")
    original_basedir = basedir.replace("\\", "/") if basedir else ""
    
    # 处理路径 - 自动转换 Windows 路径
    check_path = path
    if original_basedir and original_basedir in path:
        check_path = path.replace(original_basedir, container_prefix)
    else:
        # 自动检测并转换 Windows 路径
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
# 固化规则: 自动将 Windows 路径 (D:/xxx) 转换为容器路径 (/work/xxx)
TOOLS = [
    {
        "name": "ffmpeg-win",
        "description": "Run FFmpeg command with AUTO Windows path conversion. Paths like D:/path/file.mp4 are automatically converted to /work/path/file.mp4",
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
                    "description": "base directory (e.g. D:/tecx/text). The drive letter will be mapped to /work"
                }
            },
            "required": ["basedir", "args"]
        }
    },
    {
        "name": "imagemagick-win",
        "description": "Run ImageMagick command with AUTO Windows path conversion. Paths like D:/path/file.jpg are automatically converted",
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": "The arguments to pass to imagemagick. Windows paths are auto-converted"
                },
                "basedir": {
                    "type": "string",
                    "description": "base directory for file paths (e.g. D:/tecx/text)"
                }
            },
            "required": ["args"]
        }
    },
    {
        "name": "file-exists-win",
        "description": "Check if a file exists with AUTO Windows path conversion",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full file path (e.g. D:/tecx/text/file.jpg). Auto-converts to container path"
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
                "version": "1.1.0-auto-path-convert"
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
            # 优先使用显式传入的 basedir，否则从 args 中提取
            basedir = arguments.get("basedir", "")
            if not basedir:
                match = re.search(r'([A-Za-z]:[/\\][^\s]+)', args)
                if match:
                    basedir = match.group(1).rsplit('/', 1)[0].rsplit('\\', 1)[0]
            result = run_imagemagick(args, basedir)
            send_result(id, {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]})
        
        elif tool_name == "file-exists-win":
            path = arguments.get("path", "")
            # 从 path 中提取 basedir
            basedir = ""
            match = re.search(r'([A-Za-z]:[/\\][^\s]+)', path)
            if match:
                basedir = match.group(1).rsplit('/', 1)[0].rsplit('\\', 1)[0]
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
