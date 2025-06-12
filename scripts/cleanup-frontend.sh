#!/bin/bash

# 前端代码清理脚本
echo "🧹 开始清理前端代码..."

cd vue-frontend/src

# 1. 删除所有.DS_Store文件
echo "🗑️ 清理.DS_Store文件..."
find . -name ".DS_Store" -type f -delete

# 2. 清理重复的console.log (保留重要的错误日志)
echo "🔧 清理调试console.log..."

# 定义要保留的重要日志关键词
KEEP_PATTERNS=(
    "console.error"
    "console.warn" 
    "console.info"
    "console.debug"
    "❌"
    "⚠️"
    "💥"
    "Error"
    "Failed"
    "Exception"
)

# 创建正则表达式来匹配要保留的日志
KEEP_REGEX=""
for pattern in "${KEEP_PATTERNS[@]}"; do
    if [ -z "$KEEP_REGEX" ]; then
        KEEP_REGEX="($pattern)"
    else
        KEEP_REGEX="$KEEP_REGEX|($pattern)"
    fi
done

# 备份原文件并清理console.log
find . -name "*.ts" -o -name "*.vue" -o -name "*.js" | while read file; do
    # 检查文件是否包含console.log
    if grep -q "console\.log" "$file"; then
        echo "处理文件: $file"
        
        # 创建临时文件
        temp_file=$(mktemp)
        
        # 保留重要的console.log，移除其他的
        while IFS= read -r line; do
            if [[ $line =~ console\.log ]]; then
                # 检查是否包含要保留的关键词
                if echo "$line" | grep -qE "$KEEP_REGEX"; then
                    echo "$line" >> "$temp_file"
                else
                    # 将console.log行注释掉而不是完全删除，便于后续检查
                    echo "    // CLEANED: $line" >> "$temp_file"
                fi
            else
                echo "$line" >> "$temp_file"
            fi
        done < "$file"
        
        # 替换原文件
        mv "$temp_file" "$file"
    fi
done

echo "✅ 前端代码清理完成！"
echo ""
echo "📊 清理统计："
echo "   - 已删除所有.DS_Store文件"
echo "   - 已清理非关键console.log语句"
echo "   - 保留了错误和警告相关的日志"
echo ""
echo "⚠️ 注意：被清理的console.log已注释，请检查后手动删除注释行" 