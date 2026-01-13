FROM ccr.ccs.tencentyun.com/z5882852/python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev libpq-dev pkg-config tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*


# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令：先运行迁移，再启动服务
CMD ["sh", "-c", "python init_db.py && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
