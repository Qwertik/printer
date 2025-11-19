import os
import requests

os.makedirs('fonts', exist_ok=True)

fonts = {
    'fonts/Kings-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/kings/Kings-Regular.ttf'
}

for path, url in fonts.items():
    print(f"Downloading {url} to {path}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        print("Success.")
    except Exception as e:
        print(f"Failed: {e}")
