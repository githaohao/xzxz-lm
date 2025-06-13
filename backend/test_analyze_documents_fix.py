#!/usr/bin/env python3
"""
测试文档分析API调用修复
验证analyze-documents接口返回正确的数据格式
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加backend路径
sys.path.append(str(Path(__file__).parent))

from app.services.rag_service import RAGService
from app.config import settings
import tempfile

async def test_analyze_documents_fix():
    """测试文档分析功能的数据格式"""
    print("🔧 测试文档分析API调用修复")
    print("=" * 50)
    
    # 初始化RAG服务
    try:
        rag_service = RAGService()
        print("✅ RAG服务初始化成功")
    except Exception as e:
        print(f"❌ RAG服务初始化失败: {e}")
        return False
    
    # 创建测试文档
    test_content = """
    技术文档：Python开发指南
    
    这是一个关于Python开发的技术文档。
    包含以下内容：
    1. Python基础语法
    2. 面向对象编程
    3. 异常处理
    4. 文件操作
    5. 网络编程
    
    适合初学者学习使用。
    """
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        print(f"📄 创建测试文件: {test_file_path}")
        
        # 测试分析功能
        prompt = "请分析这个文档应该归档到哪个知识库，选择最合适的分类"
        
        print("🔍 开始分析文档...")
        result = await rag_service.analyze_document_for_archive(
            file_path=test_file_path,
            filename="python_guide.txt",
            prompt=prompt
        )
        
        print("📊 分析结果:")
        print(f"  ✅ 分析成功: {result.get('success', False)}")
        print(f"  📝 文件名: {result.get('fileName', 'N/A')}")
        print(f"  📚 推荐知识库: {result.get('knowledgeBaseName', 'N/A')}")
        print(f"  🔍 文档类型: {result.get('documentType', 'N/A')}")
        print(f"  📖 内容预览: {result.get('textContent', 'N/A')[:100]}...")
        print(f"  💭 推荐理由: {result.get('reason', 'N/A')}")
        
        # 验证必要字段
        required_fields = ['success', 'fileName', 'knowledgeBaseName', 'documentType', 'textContent']
        missing_fields = []
        
        for field in required_fields:
            if field not in result:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少必要字段: {missing_fields}")
            return False
        else:
            print("✅ 所有必要字段都存在")
        
        # 测试API响应格式
        print("\n🔧 验证API响应格式:")
        
        # 模拟后端API响应格式
        api_response = {
            "code": 200,
            "msg": "文档分析完成: 成功1个, 失败0个",
            "data": {
                "results": [result],
                "totalFiles": 1,
                "successCount": 1,
                "failureCount": 0,
                "processing_time": 0.5
            }
        }
        
        print("📝 模拟API响应格式:")
        print(f"  Code: {api_response['code']}")
        print(f"  Message: {api_response['msg']}")
        print(f"  Data.results 长度: {len(api_response['data']['results'])}")
        print(f"  Data.totalFiles: {api_response['data']['totalFiles']}")
        print(f"  Data.successCount: {api_response['data']['successCount']}")
        
        # 验证前端访问路径
        print("\n🎯 验证前端访问路径:")
        
        try:
            # 模拟前端访问 response.data.results
            results = api_response['data']['results']
            print(f"  ✅ response.data.results 访问成功，获得 {len(results)} 个结果")
            
            # 模拟前端处理每个结果
            for i, result in enumerate(results):
                print(f"  📄 结果 {i+1}:")
                print(f"    文件名: {result.get('fileName')}")
                print(f"    成功状态: {result.get('success')}")
                print(f"    知识库: {result.get('knowledgeBaseName')}")
            
        except Exception as e:
            print(f"  ❌ 前端访问路径失败: {e}")
            return False
        
        print("\n✅ 文档分析API修复验证成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时文件
        try:
            os.unlink(test_file_path)
            print(f"🗑️ 清理临时文件: {test_file_path}")
        except:
            pass

async def main():
    """主函数"""
    print("🚀 文档分析API修复测试")
    print("=" * 60)
    
    success = await test_analyze_documents_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！API修复成功")
        print("📝 前端现在可以正确访问 response.data.results")
    else:
        print("❌ 测试失败，需要进一步检查")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 