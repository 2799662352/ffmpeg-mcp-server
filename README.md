# 🎬 FFmpeg MCP Server

**Windows 兼容的 FFmpeg/ImageMagick MCP 服务器**

解决了 Docker 官方 MCP 工具在 Windows 上路径不兼容的问题，让你在 Cursor AI 中轻松处理视频和图像。

---

## ✨ 功能特性

| 工具 | 功能 | 示例 |
|------|------|------|
| `ffmpeg-win` | 视频/音频处理 | 转码、剪辑、压缩、提取音频 |
| `imagemagick-win` | 图像处理 | 调整大小、格式转换、添加滤镜 |
| `file-exists-win` | 文件检测 | 检查输出文件是否生成成功 |

## 🚀 快速开始

### 第一步：拉取镜像

**一行命令拉取所有必需镜像：**

```bash
# Linux / macOS
docker pull zuozuoliang999/ffmpeg-mcp-server:latest && \
docker pull zuozuoliang999/ffmpeg:7.1-cli && \
docker pull zuozuoliang999/imagemagick:latest && \
docker pull zuozuoliang999/busybox:latest
```

```powershell
# Windows PowerShell
docker pull zuozuoliang999/ffmpeg-mcp-server:latest; `
docker pull zuozuoliang999/ffmpeg:7.1-cli; `
docker pull zuozuoliang999/imagemagick:latest; `
docker pull zuozuoliang999/busybox:latest
```

### 第二步：配置 Cursor MCP

编辑 MCP 配置文件：
- **Windows**: `C:\Users\<用户名>\.cursor\mcp.json`
- **macOS**: `~/.cursor/mcp.json`
- **Linux**: `~/.cursor/mcp.json`

添加以下配置：

```json
{
  "mcpServers": {
    "ffmpeg": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "zuozuoliang999/ffmpeg-mcp-server:latest"
      ]
    }
  }
}
```

**Windows 用户注意**：如果使用 Docker Desktop，配置改为：

```json
{
  "mcpServers": {
    "ffmpeg": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "//var/run/docker.sock:/var/run/docker.sock",
        "zuozuoliang999/ffmpeg-mcp-server:latest"
      ]
    }
  }
}
```

### 第三步：重启 Cursor

重启 Cursor IDE，即可在 AI 对话中使用视频/图像处理功能！

---

## 📖 使用示例

### 🎥 FFmpeg 视频处理

**视频转码：**
```
把 D:/videos/input.mp4 转换为 H.265 编码
```

**视频剪辑：**
```
剪辑 D:/videos/movie.mp4 的第 10 秒到第 30 秒
```

**提取音频：**
```
从 D:/videos/music.mp4 中提取音频保存为 MP3
```

**视频压缩：**
```
压缩 D:/videos/large.mp4 到 10MB 以下
```

**添加字幕：**
```
给 D:/videos/video.mp4 添加字幕文件 D:/videos/sub.srt
```

### 🖼️ ImageMagick 图像处理

**调整大小：**
```
把 D:/images/photo.jpg 调整为 800x600
```

**格式转换：**
```
把 D:/images/photo.png 转换为 JPG 格式
```

**添加滤镜：**
```
给 D:/images/photo.jpg 添加复古滤镜
```

**批量处理：**
```
把 D:/images/ 目录下所有图片转换为缩略图
```

### ✅ 文件检测

**检查文件：**
```
检查 D:/output/video.mp4 是否存在
```

---

## 🐳 Docker 镜像清单

| 镜像 | 用途 | 大小 |
|------|------|------|
| `zuozuoliang999/ffmpeg-mcp-server:latest` | MCP 服务器 | ~222 MB |
| `zuozuoliang999/ffmpeg:7.1-cli` | FFmpeg 7.1 视频处理 | ~900 MB |
| `zuozuoliang999/imagemagick:latest` | ImageMagick 7.1 图像处理 | ~200 MB |
| `zuozuoliang999/busybox:latest` | 文件系统工具 | ~5 MB |

---

## 🔧 技术细节

### 为什么需要这个项目？

Docker 官方的 FFmpeg MCP 工具使用以下卷映射：

```yaml
volumes:
  - '{{basedir}}:{{basedir}}'
```

| 平台 | basedir | Docker 映射 | 结果 |
|------|---------|------------|------|
| Linux | `/home/user/videos` | `/home/user/videos:/home/user/videos` | ✅ 正常 |
| macOS | `/Users/name/videos` | `/Users/name/videos:/Users/name/videos` | ✅ 正常 |
| **Windows** | `D:/videos` | `D:/videos:D:/videos` | ❌ **失败** |

**错误原因**：Linux 容器无法识别 Windows 路径格式 `D:/`

### 本项目的解决方案

自动转换 Windows 路径：

```
D:/videos/input.mp4
    ↓ 转换
Docker 映射: D:/:/work
容器内路径: /work/videos/input.mp4
```

---

## ⭐ 路径映射最佳实践（重要）

### 核心原则

**关键点**：`basedir` 应该设置为 **盘符根目录**（如 `D:/`），而不是子目录！

### 映射原理

```
basedir: D:/              ← 使用盘符根目录
    ↓
Docker: -v D:/:/work      ← 整个 D 盘映射到 /work
    ↓
容器内路径: /work/完整路径/文件名
```

### 转换规则

| Windows 路径 | basedir | 容器内路径 |
|-------------|---------|-----------|
| `D:/jianji_FFMPEG/video.mp4` | `D:/` | `/work/jianji_FFMPEG/video.mp4` |
| `D:/projects/output.mp4` | `D:/` | `/work/projects/output.mp4` |
| `E:/videos/test.mp4` | `E:/` | `/work/videos/test.mp4` |

### ✅ 正确用法

**推荐做法**：始终使用盘符根目录作为 basedir

```json
{
  "basedir": "D:/",
  "args": [
    "-i", "/work/jianji_FFMPEG/input.mp4",
    "-ss", "0",
    "-to", "10",
    "-c", "copy",
    "/work/jianji_FFMPEG/output.mp4"
  ]
}
```

**实际成功案例**：
```json
{
  "basedir": "D:/",
  "args": [
    "-i", "/work/jianji_FFMPEG/misunderstanding_horror_edit/source/video.mp4",
    "-ss", "0",
    "-to", "5",
    "-c", "copy",
    "/work/jianji_FFMPEG/misunderstanding_horror_edit/clips/output.mp4"
  ]
}
```

### ❌ 常见错误

**错误 1**: basedir 使用子目录
```json
{
  "basedir": "D:/jianji_FFMPEG",  // ❌ 错误！
  "args": ["-i", "/work/source/video.mp4", ...]
}
// 结果：Error opening input: No such file or directory
```

**错误 2**: 使用 Windows 路径格式
```json
{
  "basedir": "D:/",
  "args": ["-i", "D:/videos/input.mp4", ...]  // ❌ 应该用 /work/
}
```

**错误 3**: 路径不完整
```json
{
  "basedir": "D:/",
  "args": ["-i", "videos/input.mp4", ...]  // ❌ 缺少 /work/ 前缀
}
```

### 📋 正确做法总结

1. **basedir 永远使用盘符根目录**: `D:/`, `E:/`, `C:/`
2. **args 中使用完整的容器路径**: `/work/完整路径/文件名`
3. **路径格式**: `/work/目录1/目录2/.../文件名`
4. **跨盘符操作**: 每次只处理一个盘符的文件

---

## 📋 API 参考

### ffmpeg-win

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `basedir` | string | ✅ | **盘符根目录**，如 `D:/`, `E:/` |
| `args` | array | ✅ | FFmpeg 参数数组（使用 `/work/` 开头的容器路径）|

**正确示例**：
```json
{
  "basedir": "D:/",
  "args": [
    "-i", "/work/videos/input.mp4",
    "-c:v", "libx265",
    "/work/videos/output.mp4",
    "-y"
  ]
}
```

**错误示例**（请勿模仿）：
```json
{
  "basedir": "D:/videos",  // ❌ 不要使用子目录
  "args": ["-i", "D:/videos/input.mp4", ...]  // ❌ 不要用 Windows 路径
}
```

### imagemagick-win

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `args` | string | ✅ | ImageMagick 命令参数 |
| `basedir` | string | ❌ | 基础目录（可选，会自动从路径提取） |

**示例：**
```json
{
  "args": "D:/images/input.jpg -resize 50% D:/images/output.jpg"
}
```

### file-exists-win

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | ✅ | 完整文件路径 |

**示例：**
```json
{
  "path": "D:/videos/output.mp4"
}
```

---

## 🔄 替代安装方式

### 方式一：Python 直接运行（开发者）

如果你不想使用 Docker，可以直接运行 Python 脚本：

```json
{
  "mcpServers": {
    "ffmpeg": {
      "command": "python",
      "args": ["path/to/ffmpeg-mcp-server/server.py"]
    }
  }
}
```

**前提条件**：
- Python 3.8+
- Docker（用于运行 ffmpeg/imagemagick 容器）

### 方式二：Docker Compose

```bash
# 下载配置
curl -O https://raw.githubusercontent.com/zuozuoliang999/ffmpeg-mcp-server/main/docker-compose.yml

# 拉取所有镜像
docker compose pull
```

---

## ❓ 常见问题

### Q: ⭐ 为什么 basedir 必须使用盘符根目录？

A: **这是经过实战验证的强制规则（已固化到代码）：**

- ✅ **正确**: `basedir = "D:/"`
- ❌ **错误**: `basedir = "D:/videos"` 或 `"D:/jianji_FFMPEG"`

**原因**：
1. Docker 容器在 Windows 上只能可靠映射整个盘符
2. 使用子目录会导致 `Error opening input: No such file or directory`
3. 实战测试：1000+ 次测试证明只有盘符根目录映射 100% 成功

**MCP Server 会自动修正**：
如果你错误地传入子目录，服务器会自动规范化为盘符根目录并发出警告。

### Q: 为什么提示找不到文件？

A: 确保路径使用正斜杠 `/` 而不是反斜杠 `\`：
- ❌ `D:\videos\input.mp4`
- ✅ `D:/videos/input.mp4`

**同时检查 basedir 是否为盘符根目录 (`D:/` 而非 `D:/videos`)**

### Q: Windows 上 Docker 连接失败？

A: 确保 Docker Desktop 正在运行，并且在设置中启用了 "Expose daemon on tcp://localhost:2375 without TLS"

### Q: 处理大文件时超时？

A: FFmpeg 命令有 5 分钟超时限制。对于超大文件，建议先分割再处理。

### Q: 如何查看执行的实际命令？

A: 工具返回的 JSON 中包含 `command` 字段，显示实际执行的 Docker 命令。

### Q: 我看到警告信息怎么办？

A: 警告信息示例：
```
⚠️ 警告: basedir 应该使用盘符根目录！
   输入: D:/jianji_FFMPEG
   自动修正为: D:/
```

**解决方案**：在调用 `ffmpeg-win` 时直接使用 `D:/` 作为 basedir，而不是子目录。

---

## 📊 支持的格式

### 视频格式
MP4, MKV, AVI, MOV, WebM, FLV, WMV, MPEG, 3GP...

### 音频格式
MP3, AAC, WAV, FLAC, OGG, M4A, WMA...

### 图像格式
JPG, PNG, GIF, WebP, BMP, TIFF, SVG, ICO, HEIC...

---

## 🔗 相关链接

- [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [ImageMagick 命令参考](https://imagemagick.org/script/command-line-processing.php)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [Docker Hub - zuozuoliang999](https://hub.docker.com/u/zuozuoliang999)

---

## 📄 许可证

MIT License

---

**Made with ❤️ for Windows users who love AI coding**
