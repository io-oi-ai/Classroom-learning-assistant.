FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY ./requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY ./app.py .

# 创建必要的目录
RUN mkdir -p uploads data

# 设置环境变量 - 修改PORT为10000
ENV HOST=0.0.0.0
ENV PORT=10000
ENV GOOGLE_AI_API_KEY=AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM

# 暴露端口 - 修改为10000
EXPOSE 10000

# 启动命令 - 使用PORT环境变量
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]
