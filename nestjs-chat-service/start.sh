#!/bin/bash

# 小智小智聊天历史服务启动脚本

echo "🚀 启动小智小智聊天历史服务..."

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "请复制 .env.example 为 .env 并配置相应的环境变量"
    exit 1
fi

# 检查 node_modules 是否存在
if [ ! -d node_modules ]; then
    echo "📦 安装依赖..."
    pnpm install
fi

# 构建项目
echo "🔨 构建项目..."
pnpm run build

# 启动服务
echo "🎯 启动服务..."
pnpm run start:dev 