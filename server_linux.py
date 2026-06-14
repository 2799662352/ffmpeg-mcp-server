#!/usr/bin/env python3
"""
FFmpeg MCP Server - Linux 云端版 v2.0.0

适配 Lighthouse + COSFS 部署:
- 团队 COS 桶通过 COSFS 挂载在 /home/media
- ffmpeg / imagemagick / busybox 三个工作镜像通过宿主 docker.sock 调起
- 容器内外路径完全一致 (/home/media:/home/media), 零路径转换

与 Windows 版 server.py 的区别:
- 没有 Windows 盘符 (D:/) 转换逻辑
- basedir 固定 /home/media, 工具签名里不出现 basedir 参数
- 工具名为 ffmpeg / imagemagick / file_exists (不含 -win 后缀)
"""

import subprocess
import json
import sys

MEDIA_ROOT = "/home/media"


def send(payload: dict) -> None:
    print(json.dumps(payload), flush=True)


def send_error(rid, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}})


def send_result(rid, result: dict) -> None:
    send({"jsonrpc": "2.0", "id": rid, "result": result})


def _docker_run(image: str, cmd_args: list, entrypoint: str | None = None, timeout: int = 600) -> dict:
    base = ["docker", "run", "--rm", "-v", f"{MEDIA_ROOT}:{MEDIA_ROOT}", "-w", MEDIA_ROOT]
    if entrypoint is not None:
        base.extend(["--entrypoint", entrypoint])
    docker_cmd = base + [image] + cmd_args

    try:
        proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "success": proc.returncode == 0,
            "output": proc.stdout,
            "error": proc.stderr,
            "command": " ".join(docker_cmd),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Command timeout ({timeout}s)", "command": " ".join(docker_cmd)}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "command": " ".join(docker_cmd)}


def run_ffmpeg(args: list) -> dict:
    return _docker_run("zuozuoliang999/ffmpeg:8.1-cli", list(args), timeout=600)


def run_imagemagick(args: str) -> dict:
    result = _docker_run(
        "zuozuoliang999/imagemagick:latest",
        args.split(),
        entrypoint="magick",
        timeout=300,
    )
    merged = (result.get("output") or "") + (result.get("error") or "")
    result["output"] = merged.strip() if merged.strip() else "(no output)"
    return result


def file_exists(path: str) -> dict:
    result = _docker_run("zuozuoliang999/busybox:latest", ["test", "-f", path], timeout=30)
    return {"exists": result["success"], "path": path, "command": result["command"]}


TOOLS = [
    {
        "name": "ffmpeg",
        "description": (
            f"Run FFmpeg in a sandbox container against the team-shared media volume. "
            f"All file paths MUST be absolute under `{MEDIA_ROOT}/` "
            f"(team COS bucket auto-mounted; uploaded by cos-mcp). "
            f"Typical input is `{MEDIA_ROOT}/inputs/<file>`, write outputs to `{MEDIA_ROOT}/outputs/<file>` "
            f"so they auto-sync back to the bucket. "
            f"Example args: ['-i', '{MEDIA_ROOT}/inputs/in.mp4', '-c:v', 'libx264', '-crf', '23', "
            f"'{MEDIA_ROOT}/outputs/out.mp4']"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": f"ffmpeg argv. Use absolute paths under {MEDIA_ROOT}/ for all I/O files.",
                }
            },
            "required": ["args"],
        },
    },
    {
        "name": "imagemagick",
        "description": (
            f"Run ImageMagick `magick` CLI in a sandbox container against the team-shared media volume. "
            f"All paths MUST be absolute under `{MEDIA_ROOT}/`. "
            f"Example args: '{MEDIA_ROOT}/inputs/a.png -resize 50% {MEDIA_ROOT}/outputs/a-small.png'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": f"Whitespace-separated magick arguments. Paths absolute under {MEDIA_ROOT}/.",
                }
            },
            "required": ["args"],
        },
    },
    {
        "name": "file_exists",
        "description": f"Check whether a file exists in the team-shared media volume. Path must be absolute under `{MEDIA_ROOT}/`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": f"Absolute path under {MEDIA_ROOT}/"}
            },
            "required": ["path"],
        },
    },
]


def handle_request(request: dict) -> None:
    method = request.get("method")
    rid = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        send_result(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "ffmpeg-mcp-cloud", "version": "2.0.0-linux"},
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_result(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}

        if tool_name == "ffmpeg":
            result = run_ffmpeg(arguments.get("args", []))
        elif tool_name == "imagemagick":
            result = run_imagemagick(arguments.get("args", ""))
        elif tool_name == "file_exists":
            result = file_exists(arguments.get("path", ""))
        else:
            send_error(rid, -32601, f"Unknown tool: {tool_name}")
            return

        send_result(rid, {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]})
        return

    send_error(rid, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            handle_request(request)
        except Exception as e:
            sys.stderr.write(f"handler error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
