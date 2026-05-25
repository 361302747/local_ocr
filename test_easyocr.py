import base64
import httpx

image_path = r"e:\python\local_ocr\ocr_screen\debug_red_line_color_changed.png"

with open(image_path, 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

print("Testing EasyOCR...")
with httpx.Client(timeout=60.0) as client:
    response = client.post(
        "http://localhost:8765/ocr",
        json={
            "image_base64": image_base64,
            "return_details": True
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
