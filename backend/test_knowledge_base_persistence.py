#!/usr/bin/env python3
"""
测试文档-知识库关联关系的持久化功能
验证重启程序后关联关系不会丢失
"""

import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_service import RAGService
from app.database import Database

async def test_knowledge_base_persistence():
    """测试知识库关联关系的持久化"""
    print("🧪 开始测试知识库关联关系持久化功能...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test_kb_persistence.db")
    
    try:
        # 第一阶段：创建服务实例，添加文档和知识库
        print("\n📝 第一阶段：创建数据并建立关联关系")
        
        # 设置测试环境
        os.environ['UPLOAD_DIR'] = temp_dir
        
        # 创建数据库并初始化
        db1 = Database(test_db_path)
        await db1.initialize()
        
        # 创建第一个RAG服务实例
        rag1 = RAGService()
        rag1.db = db1
        
        # 创建测试知识库
        kb1 = await rag1.create_knowledge_base(
            name="测试知识库1",
            description="用于测试持久化",
            color="#FF6B6B"
        )
        
        kb2 = await rag1.create_knowledge_base(
            name="测试知识库2", 
            description="另一个测试知识库",
            color="#4ECDC4"
        )
        
        print(f"✅ 创建知识库1: {kb1['name']} (ID: {kb1['id']})")
        print(f"✅ 创建知识库2: {kb2['name']} (ID: {kb2['id']})")
        
        # 创建测试文档
        doc1_id = await rag1.process_document(
            content="这是一个关于人工智能的测试文档。AI技术正在快速发展。",
            filename="ai_test.txt",
            file_type="text"
        )
        
        doc2_id = await rag1.process_document(
            content="这是一个关于机器学习的文档。机器学习是AI的重要分支。",
            filename="ml_test.txt", 
            file_type="text"
        )
        
        print(f"✅ 创建文档1: {doc1_id}")
        print(f"✅ 创建文档2: {doc2_id}")
        
        # 建立关联关系
        success1 = await rag1.add_documents_to_knowledge_base(kb1['id'], [doc1_id, doc2_id])
        success2 = await rag1.add_documents_to_knowledge_base(kb2['id'], [doc1_id])
        
        print(f"✅ 将文档添加到知识库1: {success1}")
        print(f"✅ 将文档1添加到知识库2: {success2}")
        
        # 验证关联关系
        kb1_docs = await rag1.get_knowledge_base_documents(kb1['id'])
        kb2_docs = await rag1.get_knowledge_base_documents(kb2['id'])
        
        print(f"📚 知识库1包含文档: {kb1_docs}")
        print(f"📚 知识库2包含文档: {kb2_docs}")
        
        # 第二阶段：销毁实例，重新创建，验证持久化
        print("\n🔄 第二阶段：重新创建服务实例，验证数据持久化")
        
        # 销毁第一个实例
        del rag1
        
        # 创建新的RAG服务实例（模拟重启）
        rag2 = RAGService()
        rag2.db = Database(test_db_path)
        
        # 获取知识库列表
        knowledge_bases = await rag2.get_all_knowledge_bases()
        print(f"✅ 重启后获取到 {len(knowledge_bases)} 个知识库")
        
        for kb in knowledge_bases:
            print(f"  - {kb['name']} (ID: {kb['id'][:8]}...)")
        
        # 验证关联关系是否持久化
        kb1_id = next(kb['id'] for kb in knowledge_bases if kb['name'] == "测试知识库1")
        kb2_id = next(kb['id'] for kb in knowledge_bases if kb['name'] == "测试知识库2")
        
        kb1_docs_after = await rag2.get_knowledge_base_documents(kb1_id)
        kb2_docs_after = await rag2.get_knowledge_base_documents(kb2_id)
        
        print(f"📚 重启后知识库1包含文档: {kb1_docs_after}")
        print(f"📚 重启后知识库2包含文档: {kb2_docs_after}")
        
        # 第三阶段：测试关联关系操作
        print("\n🔧 第三阶段：测试关联关系操作")
        
        # 移除文档关联
        remove_success = await rag2.remove_documents_from_knowledge_base(kb2_id, [doc1_id])
        print(f"✅ 从知识库2移除文档1: {remove_success}")
        
        kb2_docs_final = await rag2.get_knowledge_base_documents(kb2_id)
        print(f"📚 移除后知识库2包含文档: {kb2_docs_final}")
        
        # 第四阶段：再次重启验证
        print("\n🔄 第四阶段：再次重启验证关联关系变更")
        
        del rag2
        
        rag3 = RAGService()
        rag3.db = Database(test_db_path)
        
        kb2_docs_final_check = await rag3.get_knowledge_base_documents(kb2_id)
        print(f"📚 再次重启后知识库2包含文档: {kb2_docs_final_check}")
        
        # 验证结果
        print("\n✅ 测试结果验证:")
        
        # 验证知识库1的关联关系保持不变
        if set(kb1_docs) == set(kb1_docs_after):
            print("✅ 知识库1的关联关系在重启后保持不变")
        else:
            print("❌ 知识库1的关联关系在重启后发生变化")
            return False
        
        # 验证知识库2的关联关系正确移除
        if len(kb2_docs_final_check) == 0:
            print("✅ 文档从知识库2中正确移除并持久化")
        else:
            print("❌ 文档移除操作未正确持久化")
            return False
        
        print("\n🎉 所有测试通过！文档-知识库关联关系持久化功能正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️  清理临时目录失败: {e}")

async def main():
    """主函数"""
    print("🚀 文档-知识库关联关系持久化测试")
    print("=" * 50)
    
    success = await test_knowledge_base_persistence()
    
    if success:
        print("\n✅ 测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 