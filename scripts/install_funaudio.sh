#!/bin/bash

# 🎤 FunAudioLLM & SenseVoice 自动安装脚本
# 适用于 macOS 和 Linux 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统类型
detect_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SYSTEM="macos"
        log_info "检测到 macOS 系统"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        SYSTEM="linux"
        log_info "检测到 Linux 系统"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查 Python 版本
check_python() {
    log_info "检查 Python 版本..."
    
    # 优先检查 conda 环境的 Python
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_info "使用 conda Python 版本: $PYTHON_VERSION"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_info "使用系统 Python 版本: $PYTHON_VERSION"
    else
        log_error "未找到 Python，请先安装 Python"
        exit 1
    fi
    
    # 检查版本是否在支持范围内 (需要 3.8-3.11)
    if $PYTHON_CMD -c "
import sys
major = sys.version_info.major
minor = sys.version_info.minor
exit(0 if major == 3 and 8 <= minor <= 11 else 1)
"; then
        log_success "Python 版本符合要求"
    else
        log_error "Python 版本不符合要求，需要 3.8-3.11，当前版本: $PYTHON_VERSION"
        exit 1
    fi
}

# 检查加速器支持
check_accelerator() {
    log_info "检查硬件加速支持..."
    
    # 检查是否是 Apple Silicon
    if [[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) == "arm64" ]]; then
        CHIP_INFO=$(system_profiler SPHardwareDataType | grep "Chip:" | awk -F': ' '{print $2}')
        log_success "检测到 Apple Silicon: $CHIP_INFO"
        log_info "将使用 Metal Performance Shaders (MPS) 加速"
        USE_MPS=true
        USE_CUDA=false
    elif command -v nvidia-smi &> /dev/null; then
        CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' | head -1)
        log_success "检测到 CUDA: $CUDA_VERSION"
        USE_CUDA=true
        USE_MPS=false
    else
        log_warning "未检测到硬件加速，将使用 CPU 模式"
        USE_CUDA=false
        USE_MPS=false
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if [[ "$SYSTEM" == "macos" ]]; then
        # macOS 使用 Homebrew
        if ! command -v brew &> /dev/null; then
            log_error "未找到 Homebrew，请先安装: https://brew.sh/"
            exit 1
        fi
        
        log_info "安装 ffmpeg 和 libsndfile..."
        brew install ffmpeg libsndfile
        
    elif [[ "$SYSTEM" == "linux" ]]; then
        # Linux 使用包管理器
        if command -v apt-get &> /dev/null; then
            log_info "使用 apt-get 安装依赖..."
            sudo apt-get update
            sudo apt-get install -y ffmpeg libsndfile1 libsndfile1-dev
        elif command -v yum &> /dev/null; then
            log_info "使用 yum 安装依赖..."
            sudo yum install -y ffmpeg libsndfile libsndfile-devel
        else
            log_warning "未识别的包管理器，请手动安装 ffmpeg 和 libsndfile"
        fi
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建 Python 虚拟环境..."
    
    VENV_PATH="./funaudio_env"
    
    if [[ -d "$VENV_PATH" ]]; then
        log_warning "虚拟环境已存在，是否重新创建? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_PATH"
        else
            log_info "使用现有虚拟环境"
            return
        fi
    fi
    
    $PYTHON_CMD -m venv "$VENV_PATH"
    log_success "虚拟环境创建完成: $VENV_PATH"
}

# 激活虚拟环境
activate_venv() {
    log_info "激活虚拟环境..."
    source ./funaudio_env/bin/activate
    log_success "虚拟环境已激活"
}

# 安装 PyTorch
install_pytorch() {
    log_info "安装 PyTorch..."
    
    if [[ "$USE_MPS" == true ]]; then
        log_info "安装支持 Apple Silicon MPS 的 PyTorch..."
        # Apple Silicon 优化版本
        pip install torch torchvision torchaudio
        log_success "PyTorch (Apple Silicon MPS 优化) 安装完成"
    elif [[ "$USE_CUDA" == true ]]; then
        log_info "安装 CUDA 版本的 PyTorch..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        log_success "PyTorch (CUDA) 安装完成"
    else
        log_info "安装 CPU 版本的 PyTorch..."
        pip install torch torchvision torchaudio
        log_success "PyTorch (CPU) 安装完成"
    fi
}

# 安装 FunASR
install_funasr() {
    log_info "安装 FunASR 和相关依赖..."
    
    # 设置镜像源（中国用户）
    export HF_ENDPOINT=https://hf-mirror.com
    
    # 安装核心库
    pip install funasr
    pip install modelscope
    pip install soundfile
    pip install librosa
    
    # 安装音频处理库
    pip install pydub
    pip install scipy
    pip install numpy
    
    # 安装模型加载库
    pip install transformers
    pip install accelerate
    
    # 根据硬件选择运行时
    if [[ "$USE_MPS" == true ]]; then
        log_info "安装 Apple Silicon 优化运行时..."
        # Apple Silicon 不需要 onnxruntime-gpu
        pip install onnxruntime
        # 可选：安装 Apple 优化的 TensorFlow
        pip install tensorflow-macos tensorflow-metal
    elif [[ "$USE_CUDA" == true ]]; then
        log_info "安装 CUDA 优化运行时..."
        pip install onnxruntime-gpu
    else
        log_info "安装 CPU 运行时..."
        pip install onnxruntime
    fi
    
    # 安装其他依赖
    pip install ffmpeg-python
    pip install webrtcvad
    pip install aiohttp
    
    log_success "FunASR 和依赖安装完成"
}

# 更新后端依赖
update_backend_deps() {
    log_info "更新后端 requirements.txt..."
    
    BACKEND_DIR="./backend"
    REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_warning "未找到 requirements.txt，创建新文件"
        touch "$REQUIREMENTS_FILE"
    fi
    
    # 添加 FunAudioLLM 相关依赖
    cat >> "$REQUIREMENTS_FILE" << EOF

# FunAudioLLM 依赖
funasr>=1.0.0
modelscope>=1.9.0
soundfile>=0.12.1
librosa>=0.10.0
torch>=1.13.0
transformers>=4.30.0
accelerate>=0.20.0
pydub>=0.25.1
scipy>=1.9.0
ffmpeg-python>=0.2.0
webrtcvad>=2.0.10
aiohttp>=3.8.0
EOF
    
    log_success "requirements.txt 更新完成"
}

# 配置环境变量
setup_env() {
    log_info "配置环境变量..."
    
    ENV_FILE="./backend/.env"
    
    # 设置设备类型
    if [[ "$USE_MPS" == true ]]; then
        DEVICE_TYPE="mps"
        DEVICE_INFO="Apple Silicon MPS 加速"
    elif [[ "$USE_CUDA" == true ]]; then
        DEVICE_TYPE="cuda"
        DEVICE_INFO="CUDA GPU 加速"
    else
        DEVICE_TYPE="cpu"
        DEVICE_INFO="CPU 模式"
    fi
    
    # 创建或更新 .env 文件
    cat >> "$ENV_FILE" << EOF

# FunAudioLLM 配置
FUNAUDIO_MODEL_PATH=iic/SenseVoiceSmall
FUNAUDIO_DEVICE=$DEVICE_TYPE
FUNAUDIO_CACHE_DIR=./models/cache

# 硬件加速配置
USE_MPS=$USE_MPS
USE_CUDA=$USE_CUDA
DEVICE_TYPE=$DEVICE_TYPE

# 模型下载配置
HF_ENDPOINT=https://hf-mirror.com
MODELSCOPE_CACHE=./models/modelscope

# Apple Silicon 优化
PYTORCH_ENABLE_MPS_FALLBACK=1
MPS_MEMORY_FRACTION=0.8
EOF
    
    log_success "环境变量配置完成 ($DEVICE_INFO)"
}

# 更新服务配置
update_service_config() {
    log_info "更新服务配置..."
    
    SERVICE_INIT_FILE="./backend/app/services/__init__.py"
    
    # 备份原文件
    if [[ -f "$SERVICE_INIT_FILE" ]]; then
        cp "$SERVICE_INIT_FILE" "$SERVICE_INIT_FILE.backup"
        log_info "已备份原配置文件"
    fi
    
    # 创建新的配置文件
    cat > "$SERVICE_INIT_FILE" << 'EOF'
"""
语音服务配置
选择使用真实的 FunAudioLLM 服务还是模拟服务
"""

import os

# 从环境变量读取配置，默认使用真实服务
USE_REAL_FUNAUDIO = os.getenv("USE_REAL_FUNAUDIO", "true").lower() == "true"

if USE_REAL_FUNAUDIO:
    try:
        from .funaudio_service_real import funaudio_service
        print("✅ 使用真实的 FunAudioLLM 服务")
    except ImportError as e:
        print(f"⚠️ 无法加载真实服务，回退到模拟服务: {e}")
        from .funaudio_service_mock import funaudio_service
else:
    from .funaudio_service_mock import funaudio_service
    print("🔧 使用模拟的 FunAudioLLM 服务")

__all__ = ["funaudio_service"]
EOF
    
    log_success "服务配置更新完成"
}

# 测试安装
test_installation() {
    log_info "测试安装..."
    
    # 测试 Python 导入
    python -c "
import torch
print(f'PyTorch 版本: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if hasattr(torch.backends, 'mps'):
    print(f'MPS 可用: {torch.backends.mps.is_available()}')
    if torch.backends.mps.is_available():
        print('✅ Apple Silicon MPS 加速已启用')
else:
    print('MPS 不支持此版本')

# 检测最佳设备
if torch.cuda.is_available():
    device = 'cuda'
    print(f'🚀 推荐使用设备: {device}')
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = 'mps'
    print(f'🍎 推荐使用设备: {device} (Apple Silicon 加速)')
else:
    device = 'cpu'
    print(f'💻 推荐使用设备: {device}')

try:
    import funasr
    print('✅ FunASR 导入成功')
except ImportError as e:
    print(f'❌ FunASR 导入失败: {e}')
    exit(1)

try:
    import soundfile
    import librosa
    import pydub
    print('✅ 音频处理库导入成功')
except ImportError as e:
    print(f'❌ 音频处理库导入失败: {e}')
    exit(1)

print('🎉 所有依赖安装成功！')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "安装测试通过"
    else
        log_error "安装测试失败"
        exit 1
    fi
}

# 下载模型
download_models() {
    log_info "下载 SenseVoice 模型..."
    
    python -c "
import os
from funasr import AutoModel

# 设置缓存目录
cache_dir = './models/cache'
os.makedirs(cache_dir, exist_ok=True)

print('📥 开始下载 SenseVoice 模型...')
try:
    model = AutoModel(
        model='iic/SenseVoiceSmall',
        trust_remote_code=True,
        cache_dir=cache_dir,
        device='cpu'  # 仅下载，不加载到GPU
    )
    print('✅ SenseVoice 模型下载完成')
except Exception as e:
    print(f'❌ 模型下载失败: {e}')
    print('💡 模型将在首次使用时自动下载')
"
}

# 显示完成信息
show_completion() {
    log_success "🎉 FunAudioLLM 安装完成！"
    echo
    echo "📋 接下来的步骤："
    echo "1. 激活虚拟环境: source ./funaudio_env/bin/activate"
    echo "2. 启动后端服务: cd backend && python -m uvicorn app.main:app --reload --port 8000"
    echo "3. 启动前端服务: cd frontend && pnpm dev"
    echo "4. 访问测试页面: http://localhost:3000/voice-funaudio"
    echo
    echo "🔧 配置文件："
    echo "- 环境变量: backend/.env"
    echo "- 服务配置: backend/app/services/__init__.py"
    echo "- 模型缓存: ./models/cache"
    echo
    echo "📚 文档："
    echo "- 安装指南: docs/FunAudioLLM_安装指南.md"
    echo
    echo "🚀 享受 15 倍于 Whisper 的语音识别速度吧！"
}

# 主函数
main() {
    echo "🎤 FunAudioLLM & SenseVoice 自动安装脚本"
    echo "============================================"
    echo
    
    # 检查系统和环境
    detect_system
    check_python
    check_accelerator
    
    # 安装系统依赖
    install_system_deps
    
    # 创建和激活虚拟环境
    create_venv
    activate_venv
    
    # 安装 Python 依赖
    install_pytorch
    install_funasr
    
    # 更新项目配置
    update_backend_deps
    setup_env
    update_service_config
    
    # 测试安装
    test_installation
    
    # 下载模型（可选）
    log_info "是否现在下载 SenseVoice 模型? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        download_models
    else
        log_info "模型将在首次使用时自动下载"
    fi
    
    # 显示完成信息
    show_completion
}

# 运行主函数
main "$@" 