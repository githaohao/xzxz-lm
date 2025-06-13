#!/usr/bin/env python3
"""
测试两阶段智能归档功能
"""

import asyncio
import requests
import json
import base64
import os
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = "test_files"

def create_test_files():
    """创建测试文件"""
    os.makedirs(TEST_FILES_DIR, exist_ok=True)
    
    # 创建测试文本文件
    files = {
        "合同文档示例.txt": "这是一份软件开发合同，甲方委托乙方开发一套企业管理系统。合同期限为6个月，总金额为50万元。双方需要遵守相关法律法规，确保项目按时交付。",
        "技术文档示例.txt": "本文档描述了RESTful API的设计规范。包括HTTP方法的使用、状态码规范、请求响应格式等。API采用JSON格式进行数据交换，支持分页查询和错误处理。",
        "培训手册示例.txt": "新员工入职培训手册第一章：公司简介。本公司成立于2020年，专注于人工智能技术研发。培训内容包括企业文化、规章制度、技能培训等方面。"
    }
    
    for filename, content in files.items():
        file_path = os.path.join(TEST_FILES_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return list(files.keys())

def file_to_base64(file_path):
    """将文件转换为Base64编码"""
    with open(file_path, 'rb') as f:
        content = f.read()
        return base64.b64encode(content).decode('utf-8')

def test_analyze_documents():
    """测试第一阶段：文档分析"""
    print("🧠 测试阶段1: 文档分析")
    
    test_files = create_test_files()
    
    # 准备文件上传
    files = []
    for filename in test_files:
        file_path = os.path.join(TEST_FILES_DIR, filename)
        files.append(('files', (filename, open(file_path, 'rb'), 'text/plain')))
    
    data = {
        'prompt': '请分析这些文档的类型，并为每个文档推荐合适的知识库。重点关注文档内容的主题和用途。',
        'custom_analysis': 'true'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/lm/rag/analyze-documents",
            files=files,
            data=data,
            timeout=30
        )
        
        # 关闭文件句柄
        for _, (_, file_obj, _) in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 分析成功！共分析 {result['data']['totalFiles']} 个文件")
            
            analysis_results = []
            for item in result['data']['results']:
                print(f"  📄 {item['fileName']}")
                print(f"     📂 建议归档至: {item['knowledgeBaseName']}")
                print(f"     🏷️  文档类型: {item['documentType']}")
                print(f"     💡 原因: {item['reason']}")
                print(f"     🆕 新建知识库: {'是' if item['isNewKnowledgeBase'] else '否'}")
                print()
                
                analysis_results.append(item)
            
            return analysis_results
        else:
            print(f"❌ 分析失败: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ 分析出错: {e}")
        return None

def test_confirm_archive(analysis_results):
    """测试第二阶段：确认归档"""
    print("📂 测试阶段2: 确认归档")
    
    if not analysis_results:
        print("❌ 没有分析结果，无法进行归档测试")
        return False
    
    # 准备文件数据
    files_data = []
    for i, result in enumerate(analysis_results):
        file_path = os.path.join(TEST_FILES_DIR, result['fileName'])
        if os.path.exists(file_path):
            # 检测文件类型
            if result['fileName'].endswith('.txt'):
                file_type = 'text/plain'
            else:
                file_type = 'application/octet-stream'
            
            files_data.append({
                'fileName': result['fileName'],
                'fileType': file_type,
                'content': file_to_base64(file_path)
            })
    
    request_data = {
        'files': files_data,
        'analysisResults': analysis_results
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/lm/rag/confirm-smart-archive",
            json=request_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 归档成功！共归档 {result['data']['successCount']} 个文件")
            
            for item in result['data']['results']:
                if item['success']:
                    print(f"  ✅ {item['fileName']}")
                    print(f"     📂 已归档至: {item['knowledgeBaseName']}")
                    print(f"     🆔 文档ID: {item['docId']}")
                    print(f"     🆕 新建知识库: {'是' if item['isNewKnowledgeBase'] else '否'}")
                else:
                    print(f"  ❌ {item['fileName']}: {item.get('error', '未知错误')}")
                print()
            
            return True
        else:
            print(f"❌ 归档失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 归档出错: {e}")
        return False

def cleanup():
    """清理测试文件"""
    import shutil
    if os.path.exists(TEST_FILES_DIR):
        shutil.rmtree(TEST_FILES_DIR)
    print("🧹 测试文件已清理")

def main():
    """主测试函数"""
    print("🚀 开始测试两阶段智能归档功能")
    print("=" * 50)
    
    try:
        # 阶段1: 分析文档
        analysis_results = test_analyze_documents()
        
        if analysis_results:
            print("\n" + "=" * 50)
            
            # 阶段2: 确认归档
            archive_success = test_confirm_archive(analysis_results)
            
            if archive_success:
                print("\n🎉 两阶段智能归档测试全部通过！")
            else:
                print("\n❌ 归档阶段测试失败")
        else:
            print("\n❌ 分析阶段测试失败")
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 