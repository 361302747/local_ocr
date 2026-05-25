"""
OCR服务客户端示例
演示如何从其他机器调用OCR服务
"""
import base64
import httpx
from pathlib import Path
from typing import Optional, Dict, Any


class OCRClient:
    """OCR服务客户端"""
    
    def __init__(self, server_url: str = "http://localhost:8765"):
        """
        初始化客户端
        
        Args:
            server_url: OCR服务地址
        """
        self.server_url = server_url.rstrip('/')
    
    def _image_to_base64(self, image_path: str) -> str:
        """将图片文件转换为base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def recognize_local(
        self,
        image_path: str,
        return_details: bool = False,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        使用本地OCR引擎识别图片
        
        Args:
            image_path: 图片文件路径
            return_details: 是否返回详细信息（位置、置信度）
            timeout: 超时时间（秒）
        
        Returns:
            识别结果字典
        """
        image_base64 = self._image_to_base64(image_path)
        
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{self.server_url}/ocr",
                json={
                    "image_base64": image_base64,
                    "return_details": return_details
                }
            )
            return response.json()
    
    def recognize_lmstudio(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        使用LMStudio识别图片（适合复杂图片）
        
        Args:
            image_path: 图片文件路径
            prompt: 自定义提示词
            system_prompt: 系统提示词
            timeout: 超时时间（秒）
        
        Returns:
            识别结果字典
        """
        image_base64 = self._image_to_base64(image_path)
        
        payload = {"image_base64": image_base64}
        if prompt:
            payload["prompt"] = prompt
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{self.server_url}/lmstudio/ocr",
                json=payload
            )
            return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{self.server_url}/health")
            return response.json()


def example_usage():
    """使用示例"""
    
    client = OCRClient(server_url="http://localhost:8765")
    
    print("=" * 50)
    print("OCR服务客户端示例")
    print("=" * 50)
    
    print("\n1. 健康检查...")
    health = client.health_check()
    print(f"服务状态: {health}")
    
    test_image = "test.png"
    if Path(test_image).exists():
        print(f"\n2. 本地OCR识别 ({test_image})...")
        result = client.recognize_local(test_image, return_details=True)
        print(f"识别结果: {result}")
        
        print(f"\n3. LMStudio OCR识别 ({test_image})...")
        result = client.recognize_lmstudio(
            test_image,
            prompt="请识别图片中的所有文字，包括标点符号。"
        )
        print(f"识别结果: {result}")
    else:
        print(f"\n测试图片 {test_image} 不存在，跳过识别测试")


if __name__ == "__main__":
    example_usage()
