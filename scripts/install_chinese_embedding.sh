#!/bin/bash

# 中文嵌入模型安装脚本
# 解决RAG检索结果为0的问题

echo "🚀 安装中文友好的嵌入模型..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python"
    exit 1
fi

# 进入后端目录
cd "$(dirname "$0")/../backend" || exit 1

echo "📦 安装/更新sentence-transformers..."
pip3 install -U sentence-transformers

echo "🇨🇳 下载中文友好的嵌入模型..."
python3 -c "
import os
from sentence_transformers import SentenceTransformer

# 设置缓存目录
os.environ['SENTENCE_TRANSFORMERS_HOME'] = './models/sentence-transformers'

models = [
    'moka-ai/m3e-base',               # 推荐：多语言，中文友好
    'shibing624/text2vec-base-chinese', # 备选：中文专用
]

for model_name in models:
    try:
        print(f'⬇️  下载模型: {model_name}')
        model = SentenceTransformer(model_name)
        print(f'✅ {model_name} 下载成功')
        
        # 测试中文编码
        test_text = '这是一个中文测试'
        embedding = model.encode(test_text)
        print(f'🧪 中文测试通过，向量维度: {embedding.shape}')
        print()
        
    except Exception as e:
        print(f'❌ {model_name} 下载失败: {e}')
        print()
"

echo "✅ 嵌入模型安装完成！"
echo ""
echo "🔧 配置说明："
echo "- 默认使用 moka-ai/m3e-base (中文友好)"
echo "- 可在 backend/app/config.py 中修改 embedding_model 参数"
echo "- 降低了默认相似度阈值至 0.3 以适应中文"
echo ""
echo "🧪 运行调试脚本测试："
echo "cd backend && python debug_rag.py"
