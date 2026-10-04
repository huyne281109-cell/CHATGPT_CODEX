# Dùng hệ điều hành Linux mini có sẵn Python
FROM python:3.10-slim

# Lệnh cài đặt ffmpeg trên máy chủ
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy code vào máy chủ
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .

# Mở cổng giao tiếp
EXPOSE 10000

# Chạy server
CMD ["gunicorn", "-b", "0.0.0.0:10000", "server:app"]
