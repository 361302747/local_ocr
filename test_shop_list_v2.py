"""
测试店铺列表图片识别 - 优化版
"""
import base64
import httpx
import json

image_path = r"e:\python\local_ocr\resource\ScreenShot_2026-04-12_030326_154.png"
server_url = "http://localhost:8765"

with open(image_path, 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

print("=" * 60)
print("店铺列表图片识别测试 - 优化版")
print("=" * 60)

# 优化后的结构化输出
print("\n结构化输出（优化prompt）...")
with httpx.Client(timeout=60.0) as client:
    response = client.post(
        f"{server_url}/lmstudio/ocr",
        json={
            "image_base64": image_base64,
            "prompt": """请仔细观察这张店铺列表截图，识别每一行的店铺信息。

每一行通常包含：
- 店铺名称（如：北俱郊外地府、最低龙凤等）
- 价格信息（数字，如：3999、5999等）
- 其他信息（如：星级、描述等）

请以JSON数组格式返回，每个元素代表一行店铺：
```json
[
  {"name": "店铺名称", "price": "价格", "other": "其他信息"},
  ...
]
```

只返回JSON数组，不要其他解释。""",
            "system_prompt": "你是一个专业的OCR识别助手，擅长识别表格和列表类图片。请准确识别每一行的结构化数据。"
        }
    )
    result = response.json()
    text = result.get('text', '')
    print(f"原始结果:\n{text}")
    
    # 尝试解析JSON
    try:
        # 提取JSON部分
        if '```json' in text:
            json_str = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            json_str = text.split('```')[1].split('```')[0].strip()
        elif '[' in text:
            start = text.find('[')
            end = text.rfind(']') + 1
            json_str = text[start:end]
        else:
            json_str = text
        
        shops = json.loads(json_str)
        print(f"\n解析成功，共 {len(shops)} 个店铺:")
        for i, shop in enumerate(shops):
            print(f"  [{i+1}] {shop}")
    except Exception as e:
        print(f"\nJSON解析失败: {e}")
