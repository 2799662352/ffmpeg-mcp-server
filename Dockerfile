# FFmpeg MCP Server - Windows 兼容版
# 镜像: zuozuoliang999/ffmpeg-mcp-server:latest
FROM python:3.11-slim

LABEL maintainer="zuozuoliang999"
LABEL description="FFmpeg MCP Server with Windows path compatibility"
LABEL version="1.0.0"

# 安装 Docker CLI（用于调用其他容器）
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制所有文件
COPY server.py .
COPY README.md .
COPY docker-compose.yml .
COPY pull-all.sh .

# MCP 服务器通过 stdio 通信
CMD ["python", "server.py"]

