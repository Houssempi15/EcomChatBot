# Jenkins Test Agent Dockerfile
# 用于运行自动化测试的Jenkins Agent

FROM python:3.11-slim

LABEL maintainer="ecom-chat-bot-team"
LABEL description="Jenkins test agent for ecom-chat-bot project"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CONDA_DIR=/opt/conda

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p ${CONDA_DIR} && \
    rm /tmp/miniconda.sh && \
    ${CONDA_DIR}/bin/conda clean -a -y

# 配置PATH
ENV PATH=${CONDA_DIR}/bin:$PATH

# 创建conda环境
RUN conda create -n ecom-chat-bot python=3.11 -y && \
    conda clean -a -y

# 设置工作目录
WORKDIR /workspace

# 复制测试依赖文件
COPY backend/tests/requirements-test.txt /tmp/requirements-test.txt

# 激活环境并安装依赖
RUN /bin/bash -c "source activate ecom-chat-bot && \
    pip install -r /tmp/requirements-test.txt && \
    rm /tmp/requirements-test.txt"

# 创建报告目录
RUN mkdir -p /workspace/reports

# 设置默认shell为bash
SHELL ["/bin/bash", "-c"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 --version || exit 1

# 默认命令
CMD ["/bin/bash"]
