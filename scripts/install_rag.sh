#!/bin/bash

# RAG功能安装脚本
# 安装ChromaDB、sentence-transformers等RAG相关依赖

echo "🚀 开始安装RAG功能依赖..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python"
    exit 1
fi

# 进入后端目录
cd "$(dirname "$0")/../backend" || exit 1

echo "📍 当前目录: $(pwd)"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔧 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "🔧 升级pip..."
pip install --upgrade pip

# 安装RAG相关依赖
echo "📦 安装ChromaDB..."
pip install chromadb>=0.4.0

echo "📦 安装sentence-transformers..."
pip install sentence-transformers>=2.2.0

echo "📦 安装langchain..."
pip install langchain>=0.0.3550

echo "📦 安装numpy..."
pip install numpy>=1.24.0

# 检查Apple Silicon优化
if [[ $(uname -m) == "arm64" ]]; then
    echo "🍎 检测到Apple Silicon，设置优化环境变量..."
    export PYTORCH_ENABLE_MPS_FALLBACK=1
    export MPS_MEMORY_FRACTION=0.8
    
    # 创建环境变量文件
    cat > .env << EOF
# Apple Silicon 优化
PYTORCH_ENABLE_MPS_FALLBACK=1
MPS_MEMORY_FRACTION=0.8

# RAG配置
RAG_ENABLED=true
CHROMA_DB_PATH=uploads/chroma_db
EMBEDDING_MODEL=moka-ai/m3e-base
EOF
    
    echo "✅ 环境变量已配置到 .env 文件"
fi

# 测试安装
echo "🧪 测试RAG依赖安装..."
python3 -c "
import chromadb
import sentence_transformers
import langchain
print('✅ ChromaDB:', chromadb.__version__)
print('✅ sentence-transformers:', sentence_transformers.__version__)
print('✅ LangChain:', langchain.__version__)
print('🎉 RAG依赖安装成功！')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 RAG功能安装完成！"
    echo ""
    echo "📋 功能特性："
    echo "  • 智能文档分块和向量化"
    echo "  • 语义检索相关文档片段"
    echo "  • 支持PDF、图片等多种文档格式"
    echo "  • 降低token消耗，提高回答准确性"
    echo ""
    echo "🚀 现在可以启动后端服务来使用RAG功能："
    echo "  cd backend && python -m app.main"
    echo ""
else
    echo "❌ RAG依赖安装失败，请检查错误信息"
    exit 1
fi
