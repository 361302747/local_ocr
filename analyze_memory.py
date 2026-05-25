"""
分析OCR服务内存占用
"""
import psutil
import os

def analyze_memory():
    pid = 21032
    
    if not psutil.pid_exists(pid):
        print(f"进程 {pid} 不存在")
        return
    
    process = psutil.Process(pid)
    
    print("=" * 60)
    print("OCR服务内存占用分析")
    print("=" * 60)
    
    mem_info = process.memory_info()
    
    print(f"\n进程ID: {pid}")
    print(f"进程名: {process.name()}")
    print(f"命令行: {' '.join(process.cmdline())}")
    
    print("\n" + "-" * 60)
    print("内存使用详情:")
    print("-" * 60)
    
    rss_mb = mem_info.rss / (1024 * 1024)
    vms_mb = mem_info.vms / (1024 * 1024)
    
    print(f"RSS (实际物理内存): {rss_mb:.2f} MB")
    print(f"VMS (虚拟内存): {vms_mb:.2f} MB")
    
    print("\n" + "-" * 60)
    print("内存占用分析:")
    print("-" * 60)
    
    print("""
主要内存占用来源:

1. EasyOCR 模型 (~300-400 MB)
   - 中文简体模型文件
   - 文本检测模型
   - 文本识别模型

2. PyTorch/CPU 推理引擎 (~100-200 MB)
   - 模型加载和推理框架
   - CPU模式下的张量运算

3. FastAPI/Uvicorn (~20-50 MB)
   - Web服务框架
   - ASGI服务器

4. OpenCV/NumPy (~50-100 MB)
   - 图像处理库
   - 数值计算库

5. Python解释器和其他依赖 (~50-100 MB)
   - 标准库
   - 第三方库
""")
    
    print("-" * 60)
    print("优化建议:")
    print("-" * 60)
    print("""
1. 使用GPU模式可减少CPU内存占用（需要CUDA支持）

2. 如果不需要多语言支持，可以只加载需要的语言模型

3. 对于生产环境，可以考虑：
   - 使用Docker容器限制内存
   - 实现请求队列和批处理
   - 按需加载/卸载模型
""")

if __name__ == "__main__":
    try:
        import psutil
        analyze_memory()
    except ImportError:
        print("请先安装 psutil: pip install psutil")
