#!/bin/bash

# 环境变量设置脚本
# 解决 tokenizers 并行处理警告和其他环境问题

echo "🔧 设置环境变量..."

# 设置 tokenizers 环境变量，避免并行处理警告
export TOKENIZERS_PARALLELISM=false
echo "✅ TOKENIZERS_PARALLELISM=false"

# Apple Silicon MPS 优化
if [[ $(uname -m) == "arm64" ]]; then
    echo "🍎 检测到 Apple Silicon，设置 MPS 优化..."
    export PYTORCH_ENABLE_MPS_FALLBACK=1
    export MPS_MEMORY_FRACTION=0.8
    echo "✅ PYTORCH_ENABLE_MPS_FALLBACK=1"
    echo "✅ MPS_MEMORY_FRACTION=0.8"
fi

# HuggingFace 模型下载优化
export HF_ENDPOINT=https://hf-mirror.com
echo "✅ HF_ENDPOINT=https://hf-mirror.com"

# 显示当前环境变量
echo ""
echo "📋 当前环境变量："
echo "TOKENIZERS_PARALLELISM=$TOKENIZERS_PARALLELISM"
echo "PYTORCH_ENABLE_MPS_FALLBACK=$PYTORCH_ENABLE_MPS_FALLBACK"
echo "MPS_MEMORY_FRACTION=$MPS_MEMORY_FRACTION"
echo "HF_ENDPOINT=$HF_ENDPOINT"

echo ""
echo "🚀 环境变量设置完成！"
echo "💡 使用方法："
echo "   source scripts/set_env.sh"
echo "   cd backend && python -m app.main" 