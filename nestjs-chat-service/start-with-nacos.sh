#!/bin/bash

# 小智小智聊天历史服务启动脚本（带 Nacos 注册）
# 作者: AI助手
# 日期: 2025-06-07

echo "🚀 启动小智小智聊天历史服务..."
echo "📋 配置信息:"
echo "   - 服务端口: 3002"
echo "   - Nacos 地址: nacos:8848"
echo "   - 数据库: 192.168.10.188:3306"
echo "   - 服务名: xzxz-chat-service"
echo ""

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "💡 请先复制 .env.example 到 .env 并配置相关参数"
    exit 1
fi

# 检查 Nacos 连接
echo "🔍 检查 Nacos 连接..."
if curl -s --connect-timeout 5 http://nacos:8848/nacos/v1/ns/operator/metrics > /dev/null; then
    echo "✅ Nacos 服务可访问"
else
    echo "❌ 警告: Nacos 服务不可访问，服务仍会启动但无法注册"
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
if node scripts/test-db-connection.js > /dev/null 2>&1; then
    echo "✅ 数据库连接正常"
else
    echo "❌ 警告: 数据库连接失败，请检查配置"
fi

echo ""
echo "🎯 启动服务..."
echo "📝 提示: 按 Ctrl+C 停止服务"
echo "🌐 健康检查: http://localhost:3002/chat/health"
echo "📚 API 文档: http://localhost:3002/chat"
echo ""

# 启动服务
pnpm run start:dev 