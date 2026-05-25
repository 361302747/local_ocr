"""
测试 LMStudio OCR 功能
"""
import asyncio
import base64
from pathlib import Path
from lmstudio_client import get_lmstudio_client

async def test_lmstudio_ocr():
    """测试 LMStudio OCR"""
    print("=" * 50)
    print("测试 LMStudio OCR 功能")
    print("=" * 50)
    
    client = get_lmstudio_client()
    
    # 查找测试图片
    test_images = list(Path("resource").glob("*.png")) + list(Path("resource").glob("*.jpg"))
    
    if not test_images:
        print("未找到测试图片")
        return
    
    test_image = test_images[0]
    print(f"\n测试图片: {test_image}")
    
    # 转换为base64
    with open(test_image, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"图片大小: {len(image_base64)} 字符")
    
    print("\n执行 OCR 识别...")
    result = await client.recognize_image(
        image_base64=image_base64,
        prompt="请识别图片中的所有文字内容，只返回识别结果。"
    )
    
    print(f"\n识别结果:")
    print(f"成功: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"识别文字: {result.get('text', '')}")
    else:
        print(f"错误: {result.get('error', '')}")

if __name__ == "__main__":
    asyncio.run(test_lmstudio_ocr())
