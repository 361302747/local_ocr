"""
测试OCR服务 - 对比本地OCR和LMStudio OCR识别结果
"""
import base64
import httpx
import json
from datetime import datetime
from pathlib import Path


def test_ocr():
    image_path = r"e:\python\local_ocr\ocr_screen\debug_red_line_color_changed.png"
    server_url = "http://localhost:8765"
    
    expected_text = "师门库存物资不足，帮门派找回一个风水混元丹。(找寻到77品质以上的可以获得更多奖励)。当前任务第5次。"
    
    print("=" * 60)
    print("OCR服务测试")
    print("=" * 60)
    print(f"图片路径: {image_path}")
    print(f"期望结果: {expected_text}")
    print("=" * 60)
    
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    results = {
        "image_path": image_path,
        "expected_text": expected_text,
        "test_time": datetime.now().isoformat(),
        "results": {}
    }
    
    print("\n1. 测试本地OCR (EasyOCR)...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{server_url}/ocr",
                json={
                    "image_base64": image_base64,
                    "return_details": True
                }
            )
            ocr_result = response.json()
            print(f"状态: {ocr_result.get('success')}")
            print(f"引擎: {ocr_result.get('engine')}")
            print(f"识别结果: {ocr_result.get('text')}")
            if ocr_result.get('details'):
                print(f"详细信息: {len(ocr_result.get('details', []))} 个文本块")
                for i, detail in enumerate(ocr_result.get('details', [])[:5]):
                    print(f"  [{i+1}] {detail['text']} (置信度: {detail['confidence']:.2f})")
            
            results["results"]["easyocr"] = {
                "success": ocr_result.get('success'),
                "engine": ocr_result.get('engine'),
                "text": ocr_result.get('text'),
                "details": ocr_result.get('details'),
                "error": ocr_result.get('error')
            }
    except Exception as e:
        print(f"本地OCR测试失败: {e}")
        results["results"]["easyocr"] = {"success": False, "error": str(e)}
    
    print("\n" + "-" * 60)
    print("\n2. 测试LMStudio OCR...")
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{server_url}/lmstudio/ocr",
                json={
                    "image_base64": image_base64,
                    "prompt": "请识别图片中的所有文字内容，只返回识别结果，不要添加任何解释。",
                    "system_prompt": "你是一个OCR识别助手，专门识别图片中的文字。请准确识别并返回图片中的所有文字内容。"
                }
            )
            lmstudio_result = response.json()
            print(f"状态: {lmstudio_result.get('success')}")
            print(f"识别结果: {lmstudio_result.get('text')}")
            
            results["results"]["lmstudio"] = {
                "success": lmstudio_result.get('success'),
                "text": lmstudio_result.get('text'),
                "error": lmstudio_result.get('error')
            }
    except Exception as e:
        print(f"LMStudio OCR测试失败: {e}")
        results["results"]["lmstudio"] = {"success": False, "error": str(e)}
    
    output_dir = Path("e:/python/local_ocr/test_results")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ocr_test_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"测试结果已保存: {output_file}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    test_ocr()
