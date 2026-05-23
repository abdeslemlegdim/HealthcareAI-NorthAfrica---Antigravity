import requests

models = ['diabetes', 'heart_disease', 'parkinsons', 'lung_cancer', 'thyroid']
payload = {"features": [0,0,0,0,0,0,0,30]}  # sample features, adjust as appropriate

for m in models:
    try:
        r = requests.post(f'http://127.0.0.1:8001/api/v1/classical/predict/{m}', json=payload, timeout=10)
        print(m, '->', r.status_code)
        try:
            print(r.json())
        except Exception:
            print('Response text:', r.text)
    except Exception as e:
        print(m, 'request failed:', e)
