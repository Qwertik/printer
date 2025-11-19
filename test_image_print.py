import requests
import base64
from PIL import Image
import io

# Create a simple black square image
img = Image.new('RGB', (100, 100), color = 'black')
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='PNG')
img_byte_arr = img_byte_arr.getvalue()
base64_encoded_result = base64.b64encode(img_byte_arr).decode('utf-8')

payload = {
    "text": "Image Test",
    "image": base64_encoded_result,
    "cut": True
}

try:
    response = requests.post("http://localhost:5000/print", json=payload)
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
