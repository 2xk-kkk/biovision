FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 依赖单独一层：requirements.txt 不变时复用缓存，只改业务代码不必重装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# backend 与 frontend 必须保持同级目录关系，app.py 里按 ../frontend 定位静态资源
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

WORKDIR /app/backend

EXPOSE 8000

# 单 worker：SQLite 以 WAL 模式运行，多进程会争抢写锁
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
