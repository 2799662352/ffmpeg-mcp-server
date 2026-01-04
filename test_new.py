#!/usr/bin/env python3
"""测试更新后的路径转换"""

import server
import json

print('=== 测试路径转换 ===')
result = server.convert_windows_path('D:/tecx/text')
print(f'输入: D:/tecx/text')
print(f'Volume: {result[0]}')
print(f'容器路径: {result[1]}')

print()
print('=== 测试 ffmpeg ===')
result = server.run_ffmpeg(
    ['-y', '-i', 'D:/tecx/text/frame_preview.jpg', '-vf', 'hue=s=0', '-frames:v', '1', '-update', '1', 'D:/tecx/text/test_new_method.jpg'],
    'D:/tecx/text'
)
print(f'成功: {result["success"]}')
print(f'命令: {result["command"]}')































































































