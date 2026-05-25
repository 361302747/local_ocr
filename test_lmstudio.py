"""
测试 LMStudio 连接
"""
import asyncio
from lmstudio_client import get_lmstudio_client

async def test_lmstudio_connection():
    """测试 LMStudio 连接"""
    print("=" * 50)
    print("测试 LMStudio 连接")
    print("=" * 50)
    
    client = get_lmstudio_client()
    
    print(f"\nAPI地址: {client.api_url}")
    print(f"模型: {client.model}")
    print(f"超时: {client.timeout}秒")
    
    print("\n1. 执行健康检查...")
    is_available = await client.health_check()
    print(f"LMStudio服务可用: {is_available}")
    
    if not is_available:
        print("\n警告: LMStudio服务不可用，请检查：")
        print("- LMStudio是否已启动")
        print("- API地址是否正确（当前: " + client.api_url + "）")
        print("- 模型是否已加载")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_lmstudio_connection())
