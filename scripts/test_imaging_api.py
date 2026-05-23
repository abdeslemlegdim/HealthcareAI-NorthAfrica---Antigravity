import requests, io
from PIL import Image

img = Image.new('RGB', (224,224), color=(255,255,255))
buf = io.BytesIO()
img.save(buf, format='PNG')
buf.seek(0)
files = {'file': ('test.png', buf, 'image/png')}
try:
    r = requests.post('http://127.0.0.1:8001/api/v1/imaging/classify', files=files, timeout=10)
    print('Status:', r.status_code)
    try:
        print(r.json())
    except Exception as e:
        print('Response text:', r.text)
except Exception as e:
    print('Request failed:', e)
