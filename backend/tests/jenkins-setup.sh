#!/bin/bash

###############################################################################
# Jenkins 测试环境配置脚本
# 用途: 在Jenkins节点上配置测试环境
###############################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# 配置变量
###############################################################################

PYTHON_VERSION=${PYTHON_VERSION:-3.11}
CONDA_ENV=${CONDA_ENV:-ecom-chat-bot}
PROJECT_DIR=${WORKSPACE:-$(pwd)}
TEST_DIR="${PROJECT_DIR}/backend/tests"

log_info "================================"
log_info "Jenkins 测试环境配置"
log_info "================================"
log_info "Python版本: ${PYTHON_VERSION}"
log_info "Conda环境: ${CONDA_ENV}"
log_info "项目目录: ${PROJECT_DIR}"
log_info "测试目录: ${TEST_DIR}"
log_info "================================"

###############################################################################
# 1. 检查必要工具
###############################################################################

log_info "步骤1: 检查必要工具..."

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version)
    log_info "✓ Python已安装: ${PYTHON_VER}"
else
    log_error "✗ Python3未安装"
    exit 1
fi

# 检查Conda
if command -v conda &> /dev/null; then
    CONDA_VER=$(conda --version)
    log_info "✓ Conda已安装: ${CONDA_VER}"
else
    log_warn "⚠ Conda未安装，尝试使用系统Python"
    USE_CONDA=false
fi

# 检查curl
if command -v curl &> /dev/null; then
    log_info "✓ curl已安装"
else
    log_error "✗ curl未安装"
    exit 1
fi

###############################################################################
# 2. 创建/激活Conda环境
###############################################################################

if [ "${USE_CONDA}" != "false" ]; then
    log_info "步骤2: 配置Conda环境..."
    
    # 初始化conda
    eval "$(conda shell.bash hook)"
    
    # 检查环境是否存在
    if conda env list | grep -q "^${CONDA_ENV} "; then
        log_info "✓ Conda环境已存在: ${CONDA_ENV}"
    else
        log_info "创建Conda环境: ${CONDA_ENV}"
        conda create -n ${CONDA_ENV} python=${PYTHON_VERSION} -y
        log_info "✓ Conda环境创建成功"
    fi
    
    # 激活环境
    conda activate ${CONDA_ENV}
    log_info "✓ Conda环境已激活"
else
    log_info "步骤2: 使用系统Python环境"
fi

###############################################################################
# 3. 安装测试依赖
###############################################################################

log_info "步骤3: 安装测试依赖..."

cd ${TEST_DIR}

if [ -f "requirements-test.txt" ]; then
    pip install -r requirements-test.txt -q --no-cache-dir
    log_info "✓ 测试依赖安装完成"
else
    log_error "✗ 找不到 requirements-test.txt"
    exit 1
fi

###############################################################################
# 4. 创建测试配置
###############################################################################

log_info "步骤4: 创建测试配置..."

cat > .env.test.local << EOF
# Jenkins CI 测试配置
# 自动生成于: $(date)

# ============ 基础配置 ============
TEST_BASE_URL=${TEST_BASE_URL:-http://115.190.75.88:8000}
TEST_API_PREFIX=/api/v1

# ============ 超时设置 ============
TEST_REQUEST_TIMEOUT=30
TEST_LLM_REQUEST_TIMEOUT=60

# ============ 测试控制 ============
TEST_CLEANUP_AFTER_TEST=${TEST_CLEANUP_AFTER_TEST:-true}
TEST_SKIP_PERFORMANCE=${TEST_SKIP_PERFORMANCE:-true}
TEST_SKIP_SECURITY=${TEST_SKIP_SECURITY:-true}

# ============ 日志配置 ============
TEST_LOG_LEVEL=INFO

# ============ 测试数据配置 ============
TEST_TENANT_PREFIX=ci_test_${BUILD_NUMBER:-0}_

# ============ 并发设置 ============
TEST_MAX_CONCURRENT=10

# ============ Jenkins标识 ============
TEST_BUILD_NUMBER=${BUILD_NUMBER:-0}
TEST_BUILD_URL=${BUILD_URL:-}
EOF

log_info "✓ 测试配置已创建"

###############################################################################
# 5. 创建报告目录
###############################################################################

log_info "步骤5: 创建报告目录..."

mkdir -p reports/html
mkdir -p reports/coverage
mkdir -p reports/performance

log_info "✓ 报告目录已创建"

###############################################################################
# 6. 验证测试环境
###############################################################################

log_info "步骤6: 验证测试环境..."

# 检查测试环境URL
TEST_URL=${TEST_BASE_URL:-http://115.190.75.88:8000}
if curl -s -f "${TEST_URL}/health" > /dev/null 2>&1; then
    log_info "✓ 测试环境可访问: ${TEST_URL}"
else
    log_warn "⚠ 测试环境不可访问: ${TEST_URL}"
    log_warn "  请检查测试环境是否正常运行"
fi

# 检查pytest
if python -m pytest --version > /dev/null 2>&1; then
    PYTEST_VER=$(python -m pytest --version)
    log_info "✓ pytest已安装: ${PYTEST_VER}"
else
    log_error "✗ pytest未安装"
    exit 1
fi

###############################################################################
# 7. 显示环境信息
###############################################################################

log_info "步骤7: 环境信息..."

echo ""
echo "================================"
echo "环境配置完成"
echo "================================"
python --version
pip list | grep -E "(pytest|httpx|faker)" || true
echo "================================"
echo ""

log_info "✅ Jenkins测试环境配置完成！"
log_info ""
log_info "下一步可以运行:"
log_info "  pytest -v                    # 运行所有测试"
log_info "  pytest -m \"not slow\"        # 快速测试"
log_info "  pytest api/                  # API测试"
log_info "  ./run_tests.sh --quick       # 使用脚本"

exit 0
