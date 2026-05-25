"""
OCR引擎封装模块 - 提供统一的OCR识别接口
支持EasyOCR、Tesseract两种引擎
"""
import cv2
import numpy as np
import base64
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EasyOCRWrapper:
    """EasyOCR包装类"""
    
    class Output:
        DICT = "dict"
        STRING = "string"
    
    def __init__(self, languages: List[str] = None, gpu: bool = True, charset_file: str = None):
        import easyocr
        self.languages = languages or ['ch_sim']
        self.allowlist = None
        
        if charset_file:
            charset_path = Path(charset_file)
            if charset_path.exists():
                with open(charset_path, 'r', encoding='utf-8') as f:
                    chars = [line.strip() for line in f if line.strip()]
                self.allowlist = ''.join(chars)
                logger.info(f"[EasyOCR] 加载字符集: {charset_file}, 共 {len(self.allowlist)} 个字符")
            else:
                logger.warning(f"[EasyOCR] 字符集文件不存在: {charset_file}")
        
        self.reader = easyocr.Reader(self.languages, gpu=gpu)
        logger.info(f"[EasyOCR] 初始化完成 (languages: {self.languages}, GPU: {gpu}, allowlist: {len(self.allowlist) if self.allowlist else 'None'})")
    
    def image_to_data(self, image, config='', output_type=Output.DICT):
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        results = self.reader.readtext(image_rgb, detail=1)
        
        data = {
            'text': [],
            'left': [],
            'top': [],
            'width': [],
            'height': [],
            'conf': []
        }
        
        for (bbox, text, conf) in results:
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            left = int(min(x_coords))
            top = int(min(y_coords))
            width = int(max(x_coords) - left)
            height = int(max(y_coords) - top)
            
            data['text'].append(text)
            data['left'].append(left)
            data['top'].append(top)
            data['width'].append(width)
            data['height'].append(height)
            data['conf'].append(conf * 100)
        
        return data
    
    def image_to_string(self, image, config=''):
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        results = self.reader.readtext(image_rgb, detail=0)
        return '\n'.join(results)
    
    def readtext(self, image, detail: int = 1):
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        return self.reader.readtext(image_rgb, detail=detail, allowlist=self.allowlist)


class OCREngine:
    """OCR引擎管理类 - 单例模式"""
    
    _instance: Optional['OCREngine'] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        engine_type: str = "easyocr",
        languages: List[str] = None,
        use_gpu: bool = False,
        tesseract_cmd: Optional[str] = None,
        charset_file: Optional[str] = None
    ):
        if OCREngine._initialized:
            return
        
        self.engine_type = engine_type.lower()
        self.languages = languages or ['ch_sim']
        self.use_gpu = use_gpu
        self.tesseract_cmd = tesseract_cmd
        self.charset_file = charset_file
        
        self._engine = None
        self._actual_engine_type = None
        
        self._init_engine()
        OCREngine._initialized = True
    
    def _init_engine(self):
        """初始化底层OCR引擎"""
        if self.engine_type == 'easyocr':
            if self._init_easyocr():
                return
            logger.warning("[OCREngine] EasyOCR初始化失败，尝试Tesseract...")
        
        if self._init_tesseract():
            return
        
        logger.error("[OCREngine] 警告: 没有可用的OCR引擎")
        self._engine = None
        self._actual_engine_type = None
    
    def _init_easyocr(self) -> bool:
        """初始化EasyOCR引擎"""
        try:
            import easyocr
            
            logger.info(f"[OCREngine] EasyOCR使用{'GPU' if self.use_gpu else 'CPU'}模式")
            
            self._engine = EasyOCRWrapper(
                self.languages,
                gpu=self.use_gpu,
                charset_file=self.charset_file
            )
            self._actual_engine_type = 'easyocr'
            logger.info("[OCREngine] EasyOCR初始化成功")
            return True
        
        except ImportError as e:
            logger.error(f"[OCREngine] EasyOCR未安装: {e}")
            return False
        except Exception as e:
            logger.error(f"[OCREngine] EasyOCR初始化异常: {e}")
            return False
    
    def _init_tesseract(self) -> bool:
        """初始化Tesseract引擎"""
        try:
            import pytesseract
            import os
            
            tesseract_path = Path(self.tesseract_cmd) if self.tesseract_cmd else None
            if tesseract_path and tesseract_path.exists():
                pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
                
                system_tessdata = tesseract_path.parent / "tessdata"
                if system_tessdata.exists():
                    os.environ['TESSDATA_PREFIX'] = str(system_tessdata)
                    logger.info(f"[OCREngine] 使用系统语言包: {system_tessdata}")
                
                self._engine = pytesseract
                self._actual_engine_type = 'tesseract'
                logger.info(f"[OCREngine] Tesseract初始化成功: {self.tesseract_cmd}")
                return True
            else:
                logger.error(f"[OCREngine] Tesseract未找到: {self.tesseract_cmd}")
                return False
        
        except ImportError:
            logger.error("[OCREngine] pytesseract未安装")
            return False
        except Exception as e:
            logger.error(f"[OCREngine] Tesseract初始化异常: {e}")
            return False
    
    @property
    def is_available(self) -> bool:
        """检查OCR引擎是否可用"""
        return self._engine is not None
    
    @property
    def current_engine_type(self) -> Optional[str]:
        """获取当前实际使用的引擎类型"""
        return self._actual_engine_type
    
    def recognize(
        self,
        image: np.ndarray,
        return_details: bool = False
    ) -> Union[str, List[Tuple]]:
        """
        识别图像中的文字
        
        Args:
            image: numpy array (BGR format)
            return_details: 是否返回详细信息(bbox, text, conf)
        
        Returns:
            识别结果字符串，或详细信息列表
        """
        if self._engine is None:
            return "" if not return_details else []
        
        try:
            if self._actual_engine_type == 'easyocr':
                detail = 1 if return_details else 0
                result = self._engine.readtext(image, detail=detail)
                if return_details:
                    return result
                else:
                    return ' '.join(result) if result else ""
            else:
                if return_details:
                    data = self._engine.image_to_data(
                        image,
                        output_type=self._engine.Output.DICT
                    )
                    results = []
                    for i in range(len(data['text'])):
                        text = data['text'][i].strip()
                        if text:
                            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                            bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                            conf = data['conf'][i] / 100.0 if data['conf'][i] > 0 else 0.5
                            results.append((bbox, text, conf))
                    return results
                else:
                    return self._engine.image_to_string(image).strip()
        except Exception as e:
            logger.error(f"[OCREngine] 识别失败: {e}")
            return "" if not return_details else []


_global_ocr: Optional[OCREngine] = None


def init_ocr_engine(
    engine_type: str = "easyocr",
    languages: List[str] = None,
    use_gpu: bool = False,
    tesseract_cmd: Optional[str] = None,
    charset_file: Optional[str] = None
) -> OCREngine:
    """初始化全局OCR引擎"""
    global _global_ocr
    
    _global_ocr = OCREngine(
        engine_type=engine_type,
        languages=languages,
        use_gpu=use_gpu,
        tesseract_cmd=tesseract_cmd,
        charset_file=charset_file
    )
    return _global_ocr


def get_ocr_engine() -> Optional[OCREngine]:
    """获取全局OCR引擎实例"""
    return _global_ocr


def recognize_text(
    image: np.ndarray,
    return_details: bool = False
) -> Union[str, List[Tuple]]:
    """使用全局OCR引擎识别文字"""
    global _global_ocr
    
    if _global_ocr is None:
        logger.warning("[OCRUtil] 警告: OCR引擎未初始化")
        return "" if not return_details else []
    
    return _global_ocr.recognize(image, return_details)


def base64_to_image(base64_str: str) -> np.ndarray:
    """将base64字符串转换为numpy图像"""
    img_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


def image_to_base64(image: np.ndarray) -> str:
    """将numpy图像转换为base64字符串"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')
