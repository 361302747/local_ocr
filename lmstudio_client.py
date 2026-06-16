"""
LMStudio客户端模块 - 用于调用LMStudio的OCR识别接口
"""
import httpx
import base64
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class LMStudioClient:
    """LMStudio API客户端"""
    
    def __init__(
        self,
        api_url: str = None,
        model: str = None,
        timeout: int = None
    ):
        self.api_url = api_url or settings.lmstudio_api_url
        self.model = model or settings.lmstudio_model
        self.timeout = timeout or settings.lmstudio_timeout
        self.api_mode = settings.vlm_api_mode.lower()
    
    async def recognize_image(
        self,
        image_base64: str,
        prompt: str = "请识别图片中的所有文字内容，只返回识别结果，不要添加任何解释。",
        system_prompt: str = "你是一个OCR识别助手，专门识别图片中的文字。请准确识别并返回图片中的所有文字内容。"
    ) -> Dict[str, Any]:
        """
        使用LMStudio识别图片中的文字
        
        Args:
            image_base64: base64编码的图片
            prompt: 用户提示词
            system_prompt: 系统提示词
        
        Returns:
            识别结果字典
        """
        try:
            if self.api_mode == "ollama":
                return await self._recognize_image_ollama(
                    image_base64=image_base64,
                    prompt=prompt,
                    system_prompt=system_prompt
                )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.1
                }
                
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "text": text,
                        "raw_response": result
                    }
                else:
                    logger.error(f"[LMStudio] API调用失败: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API调用失败: {response.status_code}",
                        "text": ""
                    }
        
        except httpx.TimeoutException:
            logger.error("[LMStudio] 请求超时")
            return {
                "success": False,
                "error": "请求超时",
                "text": ""
            }
        except Exception as e:
            logger.error(f"[LMStudio] 识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    async def _recognize_image_ollama(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: str
    ) -> Dict[str, Any]:
        """使用Ollama原生接口识别图片。"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{prompt}",
                    "images": [image_base64],
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                }

                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "text": result.get("response", ""),
                        "raw_response": result
                    }

                logger.error(f"[Ollama] API调用失败: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API调用失败: {response.status_code}",
                    "text": ""
                }

        except httpx.TimeoutException:
            logger.error("[Ollama] 请求超时")
            return {
                "success": False,
                "error": "请求超时",
                "text": ""
            }
        except Exception as e:
            logger.error(f"[Ollama] 识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    async def recognize_with_custom_prompt(
        self,
        image_base64: str,
        custom_prompt: str
    ) -> Dict[str, Any]:
        """
        使用自定义提示词识别图片
        
        Args:
            image_base64: base64编码的图片
            custom_prompt: 自定义提示词
        
        Returns:
            识别结果字典
        """
        return await self.recognize_image(
            image_base64=image_base64,
            prompt=custom_prompt
        )
    
    async def health_check(self) -> bool:
        """检查LMStudio服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                if self.api_mode == "ollama":
                    base_url = self.api_url.rsplit('/api/generate', 1)[0]
                    response = await client.get(f"{base_url}/api/tags")
                    return response.status_code == 200

                base_url = self.api_url.rsplit('/chat/completions', 1)[0]
                response = await client.get(f"{base_url}/models")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"[LMStudio] 健康检查失败: {e}")
            return False


_lmstudio_client: Optional[LMStudioClient] = None


def get_lmstudio_client() -> LMStudioClient:
    """获取LMStudio客户端实例"""
    global _lmstudio_client
    
    if _lmstudio_client is None:
        _lmstudio_client = LMStudioClient()
    
    return _lmstudio_client
