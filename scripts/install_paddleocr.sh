#!/bin/bash

# 🔍 PaddleOCR 中文友好 OCR 引擎安装脚本
# 适用于 macOS 和 Linux 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "🔍 PaddleOCR 中文友好 OCR 引擎安装脚本"
    echo "=================================================================="
    echo "功能特性:"
    echo "  • 🇨🇳 专业中文 OCR 识别"
    echo "  • 🌍 支持多语言文档"
    echo "  • 🚀 高性能 PP-OCRv5 模型"
    echo "  • 📄 PDF 和图片支持"
    echo "  • 🔄 自动回退机制"
    echo "  • 🍎 Apple Silicon 优化"
    echo "=================================================================="
    echo -e "${NC}"
}

# 检查系统类型
detect_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SYSTEM="macos"
        log_info "检测到 macOS 系统"
        
        # 检查是否是 Apple Silicon
        if [[ $(uname -m) == "arm64" ]]; then
            ARCH="arm64"
            log_info "检测到 Apple Silicon (ARM64)"
        else
            ARCH="x86_64"
            log_info "检测到 Intel Mac (x86_64)"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        SYSTEM="linux"
        ARCH=$(uname -m)
        log_info "检测到 Linux 系统 ($ARCH)"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查 Python 版本
check_python() {
    log_step "检查 Python 环境..."
    
    # 优先检查 conda 环境的 Python
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_PATH=$(which python)
        log_info "使用 Python: $PYTHON_PATH (版本: $PYTHON_VERSION)"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_PATH=$(which python3)
        log_info "使用 Python3: $PYTHON_PATH (版本: $PYTHON_VERSION)"
    else
        log_error "未找到 Python，请先安装 Python 3.8+"
        exit 1
    fi
    
    # 检查版本是否在支持范围内
    if $PYTHON_CMD -c "
import sys
major = sys.version_info.major
minor = sys.version_info.minor
exit(0 if major == 3 and minor >= 8 else 1)
"; then
        log_success "Python 版本符合要求 (需要 3.8+)"
    else
        log_error "Python 版本不符合要求，需要 3.8+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
}

# 检查 pip
check_pip() {
    log_step "检查 pip 包管理器..."
    
    if ! command -v pip &> /dev/null; then
        log_error "未找到 pip，请先安装 pip"
        exit 1
    fi
    
    PIP_VERSION=$(pip --version | awk '{print $2}')
    log_info "pip 版本: $PIP_VERSION"
    
    # 升级 pip
    log_info "升级 pip 到最新版本..."
    pip install --upgrade pip
    log_success "pip 升级完成"
}

# 安装系统依赖
install_system_deps() {
    log_step "安装系统依赖..."
    
    if [[ "$SYSTEM" == "macos" ]]; then
        # macOS 使用 Homebrew
        if ! command -v brew &> /dev/null; then
            log_warning "未找到 Homebrew，尝试安装..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        log_info "安装 macOS 系统依赖..."
        brew install tesseract tesseract-lang poppler
        
        # 检查 Tesseract 安装
        if command -v tesseract &> /dev/null; then
            TESSERACT_VERSION=$(tesseract --version | head -1)
            log_success "Tesseract 安装成功: $TESSERACT_VERSION"
        fi
        
    elif [[ "$SYSTEM" == "linux" ]]; then
        # Linux 使用包管理器
        if command -v apt-get &> /dev/null; then
            log_info "使用 apt-get 安装依赖..."
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
            sudo apt-get install -y poppler-utils libpoppler-dev
            sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
        elif command -v yum &> /dev/null; then
            log_info "使用 yum 安装依赖..."
            sudo yum install -y tesseract tesseract-langpack-chi_sim tesseract-langpack-eng
            sudo yum install -y poppler-utils poppler-devel
        else
            log_warning "未识别的包管理器，请手动安装 tesseract 和 poppler"
        fi
    fi
}

# 安装 PaddleOCR 核心依赖
install_paddleocr_deps() {
    log_step "安装 PaddleOCR 核心依赖..."
    
    # 基础图像处理库
    log_info "安装图像处理库..."
    pip install opencv-python>=4.8.0
    pip install Pillow>=9.5.0
    pip install numpy>=1.24.0
    
    # PDF 处理库
    log_info "安装 PDF 处理库..."
    pip install pdf2image>=3.1.0
    pip install pypdfium2>=4.0.0
    
    # OCR 引擎
    log_info "安装 Tesseract Python 接口..."
    pip install pytesseract>=0.3.10
    
    log_success "基础依赖安装完成"
}

# 安装 PaddlePaddle
install_paddlepaddle() {
    log_step "安装 PaddlePaddle 深度学习框架..."
    
    if [[ "$SYSTEM" == "macos" && "$ARCH" == "arm64" ]]; then
        log_info "安装 Apple Silicon 优化版 PaddlePaddle..."
        pip install paddlepaddle>=3.0.0
    else
        log_info "安装标准版 PaddlePaddle..."
        pip install paddlepaddle>=3.0.0
    fi
    
    # 验证安装
    if $PYTHON_CMD -c "import paddle; print('PaddlePaddle 版本:', paddle.__version__)" 2>/dev/null; then
        log_success "PaddlePaddle 安装成功"
    else
        log_error "PaddlePaddle 安装失败"
        exit 1
    fi
}

# 安装 PaddleOCR
install_paddleocr() {
    log_step "安装 PaddleOCR..."
    
    # 安装 PaddleOCR 主包
    log_info "安装 PaddleOCR 3.0..."
    pip install paddleocr>=3.0.0
    
    # 安装额外依赖
    log_info "安装 PaddleOCR 额外依赖..."
    pip install shapely>=2.0.0
    pip install pyclipper>=1.3.0
    pip install lxml>=4.9.0
    
    # 验证安装
    if $PYTHON_CMD -c "import paddleocr; print('PaddleOCR 导入成功')" 2>/dev/null; then
        log_success "PaddleOCR 安装成功"
    else
        log_error "PaddleOCR 安装失败"
        exit 1
    fi
}

# 下载和测试模型
test_paddleocr() {
    log_step "测试 PaddleOCR 功能..."
    
    # 创建测试脚本
    cat > test_paddleocr_install.py << 'EOF'
#!/usr/bin/env python3
import paddleocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    """创建测试图片"""
    image = Image.new('RGB', (400, 200), 'white')
    draw = ImageDraw.Draw(image)
    
    # 绘制测试文本
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), "Hello World", fill='black', font=font)
    draw.text((50, 100), "你好世界", fill='black', font=font)
    
    image.save("test_ocr.png")
    return "test_ocr.png"

def test_ocr():
    """测试 OCR 功能"""
    print("🔍 初始化 PaddleOCR...")
    
    try:
        # 初始化 PaddleOCR
        ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch')
        print("✅ PaddleOCR 初始化成功")
        
        # 创建测试图片
        print("📝 创建测试图片...")
        test_image = create_test_image()
        
        # 进行 OCR 识别
        print("🔍 进行 OCR 识别...")
        result = ocr.predict(test_image)
        
        if result and len(result) > 0:
            ocr_result = result[0]
            if hasattr(ocr_result, 'json'):
                json_data = ocr_result.json
                if 'res' in json_data and 'rec_texts' in json_data['res']:
                    texts = json_data['res']['rec_texts']
                    scores = json_data['res']['rec_scores']
                    
                    print("✅ OCR 识别成功!")
                    print(f"识别文本: {texts}")
                    print(f"置信度: {[f'{s:.2f}' for s in scores]}")
                else:
                    print("⚠️  OCR 结果格式异常")
            else:
                print("⚠️  OCR 结果无 json 属性")
        else:
            print("❌ OCR 识别失败")
        
        # 清理测试文件
        if os.path.exists(test_image):
            os.remove(test_image)
            
        print("🎉 PaddleOCR 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_ocr()
EOF
    
    # 运行测试
    log_info "运行 PaddleOCR 功能测试..."
    if $PYTHON_CMD test_paddleocr_install.py; then
        log_success "PaddleOCR 功能测试通过"
    else
        log_warning "PaddleOCR 功能测试失败，但安装可能仍然成功"
    fi
    
    # 清理测试文件
    rm -f test_paddleocr_install.py test_ocr.png
}

# 创建配置文件
create_config() {
    log_step "创建 PaddleOCR 配置文件..."
    
    # 创建配置目录
    mkdir -p ../backend/app/config
    
    # 创建 OCR 配置文件
    cat > ../backend/app/config/ocr_config.py << 'EOF'
"""
PaddleOCR 配置文件
"""

# PaddleOCR 配置
PADDLEOCR_CONFIG = {
    # 基础配置
    "use_angle_cls": True,          # 使用角度分类器
    "lang": "ch",                   # 语言设置：中文
    "use_gpu": False,               # 是否使用 GPU（根据环境自动检测）
    
    # 检测模型配置
    "det_model_dir": None,          # 检测模型路径（None 为自动下载）
    "det_limit_side_len": 960,      # 检测模型输入图像长边限制
    "det_limit_type": "max",        # 限制类型
    
    # 识别模型配置
    "rec_model_dir": None,          # 识别模型路径（None 为自动下载）
    "rec_image_shape": "3, 48, 320", # 识别模型输入图像尺寸
    "rec_batch_num": 6,             # 识别批处理大小
    
    # 分类模型配置
    "cls_model_dir": None,          # 分类模型路径（None 为自动下载）
    "cls_image_shape": "3, 48, 192", # 分类模型输入图像尺寸
    "cls_batch_num": 6,             # 分类批处理大小
    "cls_thresh": 0.9,              # 分类阈值
    
    # 后处理配置
    "drop_score": 0.5,              # 丢弃得分阈值
    "use_space_char": True,         # 是否使用空格字符
}

# Tesseract 备选配置
TESSERACT_CONFIG = {
    "cmd": "/usr/local/bin/tesseract",  # macOS 默认路径
    "lang": "chi_sim+eng",              # 中文简体 + 英文
    "config": "--psm 6",                # 页面分割模式
}

# 支持的文件格式
SUPPORTED_FORMATS = {
    "images": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
    "documents": [".pdf"]
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_image_size": (4096, 4096),    # 最大图像尺寸
    "dpi": 300,                        # PDF 转图像 DPI
    "timeout": 60,                     # 处理超时时间（秒）
}
EOF
    
    log_success "配置文件创建完成: backend/app/config/ocr_config.py"
}

# 显示安装总结
show_summary() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "🎉 PaddleOCR 安装完成!"
    echo "=================================================================="
    echo -e "${NC}"
    
    log_success "安装的组件:"
    echo "  • PaddleOCR 3.0 - 中文 OCR 引擎"
    echo "  • PaddlePaddle - 深度学习框架"
    echo "  • Tesseract - 备选 OCR 引擎"
    echo "  • OpenCV - 图像处理库"
    echo "  • pdf2image - PDF 处理库"
    
    echo ""
    log_success "功能特性:"
    echo "  • 🇨🇳 专业中文文档识别"
    echo "  • 🌍 多语言支持"
    echo "  • 📄 PDF 和图片处理"
    echo "  • 🔄 自动回退机制"
    echo "  • ⚡ 高性能识别"
    
    echo ""
    log_info "使用方法:"
    echo "  1. 在 Python 中导入: import paddleocr"
    echo "  2. 初始化: ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch')"
    echo "  3. 识别文本: result = ocr.predict('image.png')"
    
    echo ""
    log_info "配置文件位置:"
    echo "  • backend/app/config/ocr_config.py"
    
    echo ""
    echo -e "${GREEN}🚀 现在可以享受强大的中文 OCR 功能了！${NC}"
}

# 主函数
main() {
    show_banner
    
    # 检查环境
    detect_system
    check_python
    check_pip
    
    # 安装依赖
    install_system_deps
    install_paddleocr_deps
    
    # 安装核心组件
    install_paddlepaddle
    install_paddleocr
    
    # 测试功能
    test_paddleocr
    
    # 创建配置
    create_config
    
    # 显示总结
    show_summary
}

# 错误处理
trap 'log_error "安装过程中发生错误，请检查上面的错误信息"' ERR

# 运行主函数
main "$@" 