import cv2
import numpy as np
import base64

image_path = r"e:\python\local_ocr\ocr_screen\debug_red_line_color_changed.png"

print("Loading image...")
image = cv2.imread(image_path)
print(f"Image shape: {image.shape}")

print("\nTesting EasyOCR directly...")
import easyocr
reader = easyocr.Reader(['ch_sim'], gpu=False)

print("Running OCR...")
try:
    results = reader.readtext(image)
    print(f"Results: {results}")
    for bbox, text, conf in results:
        print(f"  Text: {text}, Confidence: {conf:.2f}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
