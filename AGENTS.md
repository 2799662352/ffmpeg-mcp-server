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

### Docker 镜像

- `zuozuoliang999/ffmpeg:7.1-cli` - FFmpeg 视频处理
- `zuozuoliang999/imagemagick:latest` - ImageMagick 图像处理
- `zuozuoliang999/busybox:latest` - 文件系统工具

### 开发规范

- Python 3.8+，MCP 协议 2024-11-05
- JSON-RPC 2.0 通信格式
- stdin/stdout 通信，stderr 日志
- subprocess 超时 300 秒
