#!/bin/bash
# FFmpeg MCP Server - 一键拉取所有镜像

echo "🐳 拉取 FFmpeg MCP Server 及依赖镜像..."

images=(
    "zuozuoliang999/ffmpeg-mcp-server:latest"
    "zuozuoliang999/ffmpeg:8.1-cli"
    "zuozuoliang999/imagemagick:latest"
    "zuozuoliang999/busybox:latest"
)

for image in "${images[@]}"; do
    echo ""
    echo "📦 拉取 $image"
    docker pull "$image"
done

echo ""
echo "✅ 全部完成！"
echo "现在可以在 Cursor MCP 中使用 ffmpeg-mcp-server 了"





























































































