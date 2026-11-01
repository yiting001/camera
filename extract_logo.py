#!/usr/bin/env python3
"""从 SVG 中提取嵌入的图片"""
import re
import base64
from pathlib import Path

svg_path = Path(__file__).parent / "定稿 尺寸备注-01.svg"
output_dir = Path(__file__).parent

# 读取 SVG
print("读取 SVG 文件...")
with open(svg_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找 base64 图片
pattern = r'xlink:href="data:image/(jpeg|png);base64,([^"]+)"'
matches = re.findall(pattern, content)

print(f"找到 {len(matches)} 张嵌入图片")

for i, (img_type, b64_data) in enumerate(matches):
    # 解码并保存
    img_data = base64.b64decode(b64_data)
    ext = 'jpg' if img_type == 'jpeg' else img_type
    output_path = output_dir / f"extracted_image_{i+1}.{ext}"
    
    with open(output_path, 'wb') as f:
        f.write(img_data)
    
    print(f"已保存: {output_path} ({len(img_data) / 1024 / 1024:.2f} MB)")

print("\n请查看提取的图片，告诉我 logo 在图片中的大概位置（左上角/中间等），")
print("我会帮你裁剪出 logo 并生成 SVG 和 PNG 文件。")
