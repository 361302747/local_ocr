"""
测试 CUDA 和 PyTorch
"""
import torch

print("=" * 50)
print("测试 CUDA 和 PyTorch")
print("=" * 50)

print(f"\n1. PyTorch 版本: {torch.__version__}")

cuda_available = torch.cuda.is_available()
print(f"\n2. CUDA 可用: {cuda_available}")

if cuda_available:
    print(f"\n3. CUDA 版本: {torch.version.cuda}")
    print(f"\n4. GPU 数量: {torch.cuda.device_count()}")
    print(f"\n5. 当前设备: {torch.cuda.current_device()}")
    print(f"\n6. 设备名称: {torch.cuda.get_device_name(0)}")
    
    # 测试 CUDA 计算
    print(f"\n7. 测试 CUDA 计算...")
    try:
        x = torch.rand(5, 3).cuda()
        print(f"   成功在 GPU 上创建张量:")
        print(f"   {x}")
        print(f"   设备: {x.device}")
    except Exception as e:
        print(f"   失败: {e}")
else:
    print("\nCUDA 不可用，请检查：")
    print("- NVIDIA 驱动是否正确安装")
    print("- CUDA Toolkit 是否正确安装")
    print("- PyTorch 是否是 GPU 版本")
