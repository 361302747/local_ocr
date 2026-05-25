"""
测试店铺列表图片识别 - 结构化输出
"""
import base64
import httpx
import json

image_path = r"e:\python\local_ocr\resource\ScreenShot_2026-04-12_030326_154.png"
server_url = "http://localhost:8765"

with open(image_path, 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

print("=" * 60)
print("店铺列表图片识别测试")
print("=" * 60)

# 测试1: 普通识别
print("\n1. 普通识别...")
with httpx.Client(timeout=60.0) as client:
    response = client.post(
        f"{server_url}/lmstudio/ocr",
        json={
            "image_base64": image_base64,
            "prompt": "请识别图片中的所有文字内容。",
            "system_prompt": "你是一个OCR识别助手。"
        }
    )
    result = response.json()
    print(f"结果:\n{result.get('text', '')}")

print("\n" + "-" * 60)

# 测试2: 结构化输出
print("\n2. 结构化输出（每行一个店铺）...")
with httpx.Client(timeout=60.0) as client:
    response = client.post(
        f"{server_url}/lmstudio/ocr",
        json={
            "image_base64": image_base64,
            "prompt": "这是一个店铺列表图片。请识别每一行的店铺信息，以JSON数组格式返回，每个店铺包含：店铺名称、价格、销量等字段。只返回JSON，不要其他解释。",
            "system_prompt": "你是一个专业的OCR识别助手，擅长识别结构化数据。请准确识别每一行的店铺信息，并以JSON格式返回。"
        }
    )
    result = response.json()
    print(f"结果:\n{result.get('text', '')}")

print("\n" + "-" * 60)

# 测试3: EasyOCR对比
print("\n3. EasyOCR识别（对比）...")
with httpx.Client(timeout=60.0) as client:
    response = client.post(
        f"{server_url}/ocr",
        json={
            "image_base64": image_base64,
            "return_details": True
        }
    )
    result = response.json()
    print(f"识别到 {len(result.get('details', []))} 个文本块:")
    for i, detail in enumerate(result.get('details', [])[:10]):
        print(f"  [{i+1}] {detail['text']} (置信度: {detail['confidence']:.2f})")
