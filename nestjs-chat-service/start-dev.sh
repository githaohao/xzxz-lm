#!/bin/bash

# 小智小智聊天历史服务 - 开发环境启动脚本

echo "🚀 启动小智小智聊天历史服务 (开发模式)"
echo "=================================="

# 检查Node.js版本
echo "检查Node.js环境..."
node_version=$(node -v 2>/dev/null || echo "未安装")
echo "Node.js版本: $node_version"

# 检查pnpm
echo "检查pnpm..."
pnpm_version=$(pnpm -v 2>/dev/null || echo "未安装")
echo "pnpm版本: $pnpm_version"

# 设置环境变量
export NODE_ENV=development
export PORT=3002

echo ""
echo "📦 检查依赖..."
if [ ! -d "node_modules" ]; then
    echo "依赖未安装，正在安装..."
    pnpm install
else
    echo "依赖已安装 ✅"
fi

echo ""
echo "🔨 构建项目..."
pnpm run build

echo ""
echo "🔧 环境配置:"
echo "  - 运行模式: $NODE_ENV"
echo "  - 服务端口: $PORT"
echo "  - 数据库: MySQL"
echo "  - 是否启用Nacos: ${NACOS_ENABLED:-true}"

echo ""
echo "💾 数据库配置检查..."
if [ -f ".env" ]; then
    echo "环境配置文件存在 ✅"
    echo "数据库地址: $(grep DB_HOST .env | cut -d'=' -f2)"
    echo "数据库端口: $(grep DB_PORT .env | cut -d'=' -f2)"
    echo "数据库名称: $(grep DB_DATABASE .env | cut -d'=' -f2)"
else
    echo "⚠️ 未找到.env文件，使用默认配置"
fi

echo ""
echo "🌟 启动服务..."
echo "API地址: http://localhost:$PORT"
echo "健康检查: http://localhost:$PORT/chat/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="

# 启动开发服务器
pnpm run start:dev 