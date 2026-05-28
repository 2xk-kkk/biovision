import urllib.request
import json
import urllib.parse

url = 'http://localhost:8000/api/create_post'
data = {
    'content': '测试帖子',
    'image_urls': [],
    'tag': '学习交流',
    'tags': ['学习交流']
}

headers = {
    'Content-Type': 'application/json',
    'token': 'test-token'
}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode('utf-8'))
    print("API返回:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"错误: {e}")
    try:
        # 尝试获取错误响应
        if hasattr(e, 'read'):
            print(f"错误响应: {e.read().decode('utf-8')}")
    except:
        pass