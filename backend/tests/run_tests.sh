#!/bin/bash

# 测试运行脚本
# 用法: ./run_tests.sh [选项]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}电商智能客服系统 - 测试执行${NC}"
echo -e "${GREEN}================================${NC}\n"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements-test.txt" ]; then
    echo -e "${RED}错误: 未找到requirements-test.txt${NC}"
    exit 1
fi

# 创建报告目录
mkdir -p reports/html
mkdir -p reports/coverage

# 解析参数
MODE="all"
MARKERS=""
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            MODE="quick"
            MARKERS="-m 'not slow and not performance and not security'"
            shift
            ;;
        --integration)
            MODE="integration"
            MARKERS="-m integration"
            shift
            ;;
        --performance)
            MODE="performance"
            MARKERS="-m performance"
            shift
            ;;
        --security)
            MODE="security"
            MARKERS="-m security"
            shift
            ;;
        --api)
            MODE="api"
            MARKERS="api/"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v -s"
            shift
            ;;
        --help)
            echo "用法: ./run_tests.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --quick         快速测试（跳过慢速、性能、安全测试）"
            echo "  --integration   只运行集成测试"
            echo "  --performance   只运行性能测试"
            echo "  --security      只运行安全测试"
            echo "  --api           只运行API测试"
            echo "  -v, --verbose   详细输出"
            echo "  --help          显示帮助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 显示测试模式
echo -e "${YELLOW}测试模式: ${MODE}${NC}\n"

# 检查环境配置
if [ ! -f ".env.test" ] && [ ! -f ".env.test.local" ]; then
    echo -e "${YELLOW}警告: 未找到环境配置文件${NC}"
    echo -e "${YELLOW}将使用默认配置${NC}\n"
fi

# 安装依赖（如果需要）
echo -e "${YELLOW}检查依赖...${NC}"
pip install -q -r requirements-test.txt
echo -e "${GREEN}✓ 依赖检查完成${NC}\n"

# 运行测试
echo -e "${YELLOW}开始运行测试...${NC}\n"

if [ "$MODE" = "all" ]; then
    pytest $VERBOSE \
        --html=reports/html/report.html \
        --self-contained-html \
        --cov=. \
        --cov-report=html:reports/coverage \
        --cov-report=term-missing
elif [ "$MODE" = "quick" ]; then
    pytest $VERBOSE \
        -m "not slow and not performance and not security" \
        --html=reports/html/report.html \
        --self-contained-html
else
    pytest $VERBOSE $MARKERS \
        --html=reports/html/report.html \
        --self-contained-html
fi

TEST_RESULT=$?

# 显示结果
echo ""
echo -e "${GREEN}================================${NC}"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 测试执行完成！${NC}"
else
    echo -e "${RED}❌ 测试执行失败！${NC}"
fi
echo -e "${GREEN}================================${NC}\n"

# 显示报告位置
echo -e "${YELLOW}测试报告:${NC}"
echo -e "  HTML报告: ${GREEN}reports/html/report.html${NC}"
if [ "$MODE" = "all" ]; then
    echo -e "  覆盖率报告: ${GREEN}reports/coverage/index.html${NC}"
fi
echo ""

exit $TEST_RESULT
