#!/usr/bin/env python3
"""
简单的用户绑定聊天历史系统测试
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Database

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_database():
    """测试基本数据库功能"""
    logger.info("🗄️ 测试数据库基本功能...")
    
    try:
        # 使用独立的测试数据库
        db = Database("test_simple.db")
        await db.initialize()
        
        # 测试用户创建
        user_id = 12345
        user_info = {
            "username": "test_user",
            "nickname": "测试用户",
            "email": "test@example.com"
        }
        
        success = await db.ensure_user_exists(user_id, user_info)
        if success:
            logger.info("✅ 用户创建/验证成功")
        else:
            logger.error("❌ 用户创建失败")
            return False
        
        # 测试手动创建会话
        session_id = "test-session-123"
        async with db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO chat_sessions (id, user_id, title, description)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_id, "测试会话", "这是一个测试会话"))
            await conn.commit()
            
            # 验证会话是否创建成功
            cursor = await conn.execute(
                "SELECT id, title FROM chat_sessions WHERE user_id = ?",
                (user_id,)
            )
            sessions = await cursor.fetchall()
            
            if sessions:
                logger.info(f"✅ 会话创建成功，找到 {len(sessions)} 个会话")
                for session in sessions:
                    logger.info(f"   会话: {session[0]} - {session[1]}")
            else:
                logger.error("❌ 会话创建失败")
                return False
        
        # 清理测试数据库
        os.remove("test_simple.db")
        logger.info("🧹 清理测试数据")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库测试失败: {e}")
        return False

async def test_chromadb_basic():
    """测试ChromaDB基本功能"""
    logger.info("🧠 测试ChromaDB基本功能...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        import tempfile
        import shutil
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 初始化ChromaDB
        client = chromadb.PersistentClient(
            path=temp_dir,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # 创建集合
        collection_name = "test_collection"
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"✅ ChromaDB集合创建成功: {collection_name}")
        
        # 添加测试文档
        documents = ["这是第一个测试文档", "这是第二个测试文档"]
        ids = ["doc1", "doc2"]
        metadatas = [{"type": "test"}, {"type": "test"}]
        
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        logger.info("✅ 文档添加成功")
        
        # 查询测试
        results = collection.query(
            query_texts=["测试文档"],
            n_results=2
        )
        
        if results['documents'] and results['documents'][0]:
            logger.info(f"✅ 查询成功，找到 {len(results['documents'][0])} 个文档")
        else:
            logger.error("❌ 查询失败")
            return False
        
        # 清理
        shutil.rmtree(temp_dir)
        logger.info("🧹 清理ChromaDB测试数据")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ChromaDB测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("🚀 开始基本功能测试")
    logger.info("=" * 50)
    
    tests = [
        ("数据库基本功能", test_basic_database),
        ("ChromaDB基本功能", test_chromadb_basic),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 执行测试: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("📊 测试总结")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.info("🎉 所有基本功能测试通过！")
        return True
    else:
        logger.error("⚠️ 部分测试失败。")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 