#!/bin/bash

# OCR服务 Apple Silicon 优化安装脚本
# 适用于 macOS Apple Silicon (M1/M2/M3)

echo "🚀 开始安装OCR服务优化依赖..."
echo "适用于Apple Silicon Mac (M1/M2/M3)"
echo "======================================="

# 检查系统架构
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    echo "⚠️  警告: 此脚本专为Apple Silicon设计，当前架构: $ARCH"
    read -p "是否继续安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python版本: $PYTHON_VERSION"

# 安装依赖
echo "📦 安装系统依赖..."
brew update
brew install poppler tesseract tesseract-lang

# 安装Python依赖
echo "🐍 安装Python依赖..."
python3 -m pip install --upgrade pip
python3 -m pip install paddlepaddle paddleocr
python3 -m pip install opencv-python opencv-contrib-python
python3 -m pip install Pillow pdf2image pytesseract
python3 -m pip install asyncio-pool aiofiles

echo "🎉 安装完成!"