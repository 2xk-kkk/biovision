import urllib.request
import json

response = urllib.request.urlopen('http://localhost:8000/api/posts?page=1&page_size=1')
data = json.loads(response.read().decode('utf-8'))

print("API返回的数据:")
print(json.dumps(data, indent=2, ensure_ascii=False))

if 'posts' in data and len(data['posts']) > 0:
    post = data['posts'][0]
    print(f"\n帖子的 images 字段: {post.get('images', 'NOT_FOUND')}")
    print(f"帖子的 files 字段: {post.get('files', 'NOT_FOUND')}")