
# Dockerfile
# 使用 chainguard 官方静态 Python 镜像（支持 amd64 + arm64，原生多架构）
FROM cgr.dev/chainguard/python:latest-dev AS builder
WORKDIR /app
COPY stress-py.py .
# 仅安装 pip（自带），无需编译任何东西
RUN python -m ensurepip && python -m pip install --upgrade pip

# 最终运行镜像（仅 11MB！无 shell、无 libc）
FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --from=builder /app/stress-py.py .
COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages

# 直接运行 Python 脚本
ENTRYPOINT ["python", "/app/stress-py.py"]
