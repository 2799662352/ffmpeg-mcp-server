# FFmpeg MCP Server - 一键拉取所有镜像
Write-Host "🐳 拉取 FFmpeg MCP Server 及依赖镜像..." -ForegroundColor Cyan

$images = @(
    "zuozuoliang999/ffmpeg-mcp-server:latest",
    "zuozuoliang999/ffmpeg:7.1-cli",
    "zuozuoliang999/imagemagick:latest",
    "zuozuoliang999/busybox:latest"
)

foreach ($image in $images) {
    Write-Host "`n📦 拉取 $image" -ForegroundColor Yellow
    docker pull $image
}

Write-Host "`n✅ 全部完成！" -ForegroundColor Green
Write-Host "现在可以在 Cursor MCP 中使用 ffmpeg-mcp-server 了" -ForegroundColor Green

