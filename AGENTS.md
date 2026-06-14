# AGENTS

## Project: FFmpeg MCP Server

Windows 兼容的 FFmpeg/ImageMagick MCP 服务器，解决 Docker 在 Windows 上的路径映射问题。

### MCP 工具

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `ffmpeg-win` | 视频/音频处理 | `basedir`(盘符根目录), `args`(FFmpeg 参数) |
| `imagemagick-win` | 图像处理 | `args`(ImageMagick 参数), `basedir`(可选) |
| `file-exists-win` | 文件检测 | `path`(完整文件路径) |

### 核心规则

1. **basedir 必须使用盘符根目录**: `D:/`, `E:/`, `C:/`
2. **Windows 路径自动转换**: `D:/path/file.mp4` → `/work/path/file.mp4`
3. **使用正斜杠**: `/` 而非 `\`

### Agent 技能 (`.agents/skills/`)

| 技能 | 用途 |
|------|------|
| `ffmpeg-win` | **首选**。驱动 `ffmpeg-win` MCP 工具的操作手册 — 转码/缩放/裁剪/变速/压缩/音频/拼接/缩略图/GIF/检测,全部用 `args` 数组 + 盘符根 `basedir` 的调用约定。自包含,可被 Codex 等 agent 独立安装。 |
| `ffmpeg-toolkit` | 上游 [jakenuts/ffmpeg-toolkit](https://github.com/jakenuts/agent-skills) 原样克隆(本地 `ffmpeg` 二进制语义),作为知识底料/参考。日常请用 `ffmpeg-win`。 |

调用前请加载 `ffmpeg-win/SKILL.md`:每条命令是一次 `ffmpeg-win` 调用,`args` 一词一元素、滤镜串保持完整、首位加 `-y`、`basedir` 用盘符根、路径用完整 Windows 路径;无 shell(循环/管道/重定向需多次调用);无独立 `ffprobe`(用 `ffmpeg -i` 读 stderr);超时 5 分钟。

### Docker 镜像

- `zuozuoliang999/ffmpeg:8.1-cli` - FFmpeg 视频处理
- `zuozuoliang999/imagemagick:latest` - ImageMagick 图像处理
- `zuozuoliang999/busybox:latest` - 文件系统工具

### 开发规范

- Python 3.8+，MCP 协议 2024-11-05
- JSON-RPC 2.0 通信格式
- stdin/stdout 通信，stderr 日志
- subprocess 超时 300 秒
