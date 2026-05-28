import urllib.request
import json

try:
    response = urllib.request.urlopen('http://localhost:8000/health')
    data = json.loads(response.read().decode('utf-8'))
    print("API正常:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"API错误: {e}")