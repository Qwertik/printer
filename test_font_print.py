import requests

payload = {
    "text": "This is Kings Font",
    "header": "Kings Header",
    "font_style": "kings",
    "font_size": 36,
    "align": "center",
    "bold": True,
    "cut": True
}

try:
    response = requests.post("http://localhost:5000/print", json=payload)
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
