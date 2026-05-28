import urllib.request
import json

# 测试OPTIONS请求（CORS预检请求）
url = 'http://localhost:8000/api/create_post'

print("测试CORS预检请求...")
try:
    req = urllib.request.Request(url, method='OPTIONS')
    response = urllib.request.urlopen(req, timeout=5)
    print(f"OPTIONS请求成功，状态码: {response.status}")
    print("响应头:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
except Exception as e:
    print(f"OPTIONS请求失败: {e}")

print("\n" + "="*50 + "\n")

# 测试POST请求（带token）
print("测试POST请求...")
data = {
    'content': '测试帖子',
    'image_urls': [],
    'tag': '学习交流',
    'tags': ['学习交流']
}

headers = {
    'Content-Type': 'application/json',
    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo4LCJ1c2VybmFtZSI6Inhpb25nIiwiZXhwIjoxNzAwMDAwMDAwfQ.xxx'
}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    response = urllib.request.urlopen(req, timeout=5)
    result = json.loads(response.read().decode('utf-8'))
    print(f"POST请求成功，状态码: {response.status}")
    print("响应:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"POST请求失败: {e}")