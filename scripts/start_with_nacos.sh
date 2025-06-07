#!/bin/bash

# 小智小智多模态聊天系统 - Nacos集成启动脚本
# 用于启动带有Nacos服务注册功能的AI聊天服务

set -e

echo "🚀 启动小智小智多模态聊天系统（Nacos集成版）"
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检查Python环境
echo -e "${BLUE}📋 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装，请先安装Python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python版本: ${PYTHON_VERSION}${NC}"

# 检查并设置环境变量
echo -e "${BLUE}🔧 设置环境变量...${NC}"
export TOKENIZERS_PARALLELISM=false
export PYTORCH_ENABLE_MPS_FALLBACK=1
export MPS_MEMORY_FRACTION=0.8
export OMP_NUM_THREADS=8

# 检查环境配置文件
ENV_FILE="backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  未找到环境配置文件 ${ENV_FILE}${NC}"
    echo -e "${BLUE}📝 从示例文件创建...${NC}"
    if [ -f "backend/env.example" ]; then
        cp backend/env.example "$ENV_FILE"
        echo -e "${GREEN}✅ 已创建环境配置文件${NC}"
        echo -e "${YELLOW}⚠️  请编辑 ${ENV_FILE} 文件配置您的Nacos服务器地址${NC}"
    else
        echo -e "${RED}❌ 未找到示例配置文件${NC}"
        exit 1
    fi
fi

# 检查Nacos配置
echo -e "${BLUE}🔍 检查Nacos配置...${NC}"
source "$ENV_FILE" 2>/dev/null || true

if [ "${NACOS_ENABLED:-false}" = "true" ]; then
    echo -e "${GREEN}✅ Nacos功能已启用${NC}"
    echo -e "${BLUE}   服务器地址: ${NACOS_SERVER_ADDRESSES:-127.0.0.1:8848}${NC}"
    echo -e "${BLUE}   服务名称: ${NACOS_SERVICE_NAME:-xzxz-lm-service}${NC}"
    echo -e "${BLUE}   服务分组: ${NACOS_GROUP:-DEFAULT_GROUP}${NC}"
    
    # 检查Nacos服务器连通性
    NACOS_HOST=$(echo "${NACOS_SERVER_ADDRESSES:-127.0.0.1:8848}" | cut -d':' -f1)
    NACOS_PORT=$(echo "${NACOS_SERVER_ADDRESSES:-127.0.0.1:8848}" | cut -d':' -f2)
    
    echo -e "${BLUE}🔗 检查Nacos服务器连通性...${NC}"
    if timeout 5 bash -c "</dev/tcp/${NACOS_HOST}/${NACOS_PORT}"; then
        echo -e "${GREEN}✅ Nacos服务器连接正常${NC}"
    else
        echo -e "${YELLOW}⚠️  无法连接到Nacos服务器 ${NACOS_HOST}:${NACOS_PORT}${NC}"
        echo -e "${YELLOW}   请确保Nacos服务器正在运行${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Nacos功能未启用，将以独立模式运行${NC}"
fi

# 检查依赖
echo -e "${BLUE}📦 检查Python依赖...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔧 创建虚拟环境...${NC}"
    python3 -m venv venv
fi

echo -e "${BLUE}🔧 激活虚拟环境...${NC}"
source venv/bin/activate

echo -e "${BLUE}📦 安装/更新依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 检查LM Studio
echo -e "${BLUE}🤖 检查LM Studio连接...${NC}"
LM_STUDIO_URL="${LM_STUDIO_BASE_URL:-http://127.0.0.1:1234}"
if curl -s -f "${LM_STUDIO_URL}/v1/models" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ LM Studio连接正常${NC}"
else
    echo -e "${YELLOW}⚠️  无法连接到LM Studio ${LM_STUDIO_URL}${NC}"
    echo -e "${YELLOW}   请确保LM Studio正在运行并启动了本地服务器${NC}"
fi

# 启动服务
echo -e "${BLUE}🚀 启动服务...${NC}"
echo "================================================"

# 显示启动信息
echo -e "${GREEN}🌟 服务启动信息:${NC}"
echo -e "   应用名称: ${APP_NAME:-小智小智 多模态聊天系统}"
echo -e "   服务地址: http://${HOST:-0.0.0.0}:${PORT:-8000}"
echo -e "   健康检查: http://${HOST:-0.0.0.0}:${PORT:-8000}/health"
echo -e "   服务状态: http://${HOST:-0.0.0.0}:${PORT:-8000}/status"

if [ "${DEBUG:-true}" = "true" ]; then
    echo -e "   API文档: http://${HOST:-0.0.0.0}:${PORT:-8000}/docs"
fi

if [ "${NACOS_ENABLED:-false}" = "true" ]; then
    echo -e "   ${GREEN}Nacos注册: 启用${NC}"
    echo -e "   Gateway访问: http://your-gateway:port${GATEWAY_CONTEXT_PATH:-/lm}/health"
else
    echo -e "   ${YELLOW}Nacos注册: 禁用${NC}"
fi

echo "================================================"

# 启动应用
exec python -m app.main 