"""
测试 EasyOCR GPU 模式
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ocr_engine import init_ocr_engine, get_ocr_engine, recognize_text, base64_to_image
import base64

print("=" * 50)
print("测试 EasyOCR GPU 模式")
print("=" * 50)

# 初始化 OCR 引擎
print("\n1. 初始化 OCR 引擎...")
init_ocr_engine(
    engine_type="easyocr",
    languages=["ch_sim"],
    use_gpu=True
)

engine = get_ocr_engine()

if not engine or not engine.is_available:
    print("❌ OCR 引擎初始化失败")
    sys.exit(1)

print(f"✅ OCR 引擎初始化成功: {engine.current_engine_type}")

# 测试图片
test_image = Path("resource/ScreenShot_2026-04-12_030326_154.png")
if test_image.exists():
    print(f"\n2. 测试 OCR 识别: {test_image}")
    
    with open(test_image, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    image = base64_to_image(image_base64)
    
    result = recognize_text(image, return_details=False)
    
    print(f"\n识别结果:")
    print(result)
