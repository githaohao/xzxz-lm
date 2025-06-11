/**
 * 对话彻底同步功能测试工具
 * 用于验证云端不存在对话的完全清除功能（选项B）
 */

import type { Conversation, ChatSession } from '@/types'

// 模拟的本地对话数据
const mockLocalConversations: Conversation[] = [
  {
    id: 'local-1',
    title: '已同步但云端已删除的对话',
    createdAt: new Date('2025-06-10T10:00:00Z'),
    updatedAt: new Date('2025-06-10T10:00:00Z'),
    messageCount: 5,
    isActive: false,
    historySessionId: 'deleted-session-1', // 这个在云端已被删除
    lastMessage: '这个对话在云端已被删除'
  },
  {
    id: 'local-2', 
    title: '云端存在的对话',
    createdAt: new Date('2025-06-10T11:00:00Z'),
    updatedAt: new Date('2025-06-10T11:00:00Z'),
    messageCount: 3,
    isActive: false,
    historySessionId: 'existing-session-1', // 这个在云端存在
    lastMessage: '这个对话在云端存在'
  },
  {
    id: 'local-3',
    title: '纯本地对话1',
    createdAt: new Date('2025-06-10T12:00:00Z'),
    updatedAt: new Date('2025-06-10T12:00:00Z'),
    messageCount: 2,
    isActive: false,
    // 没有historySessionId，纯本地对话
    lastMessage: '这是纯本地对话，将被删除'
  },
  {
    id: 'local-4',
    title: '另一个纯本地对话',
    createdAt: new Date('2025-06-10T13:00:00Z'),
    updatedAt: new Date('2025-06-10T13:00:00Z'),
    messageCount: 1,
    isActive: true,
    // 没有historySessionId，纯本地对话
    lastMessage: '另一个纯本地对话，也将被删除'
  }
]

// 模拟的云端会话数据（只有部分对话存在）
const mockRemoteSessions: ChatSession[] = [
  {
    id: 'existing-session-1', // 这个对话在本地存在
    title: '云端存在的对话',
    description: '这个对话在云端存在',
    createdAt: '2025-06-10T11:00:00Z',
    updatedAt: '2025-06-10T11:00:00Z',
    messageCount: 3,
    tags: ['chat', 'ai', 'conversation']
  },
  {
    id: 'new-session-1', // 这是云端新增的对话，本地没有
    title: '云端新增的对话',
    description: '这是云端新增的对话',
    createdAt: '2025-06-11T14:00:00Z',
    updatedAt: '2025-06-11T14:00:00Z',
    messageCount: 1,
    tags: ['chat', 'ai', 'conversation']
  }
]

/**
 * 测试彻底同步逻辑（选项B）
 */
export function testThoroughSyncLogic() {
  console.log('🧪 开始测试对话彻底同步逻辑（选项B）...')
  console.log('=' .repeat(60))
  
  // 创建远程会话ID集合
  const remoteSessionIds = new Set(mockRemoteSessions.map(session => session.id))
  console.log('☁️ 云端会话ID:', Array.from(remoteSessionIds))
  
  // 按照新逻辑：清除所有云端不存在的对话
  const conversationsToRemove = mockLocalConversations.filter(conv => {
    // 如果对话有historySessionId，检查云端是否存在
    if (conv.historySessionId) {
      return !remoteSessionIds.has(conv.historySessionId)
    }
    // 如果是纯本地对话（没有historySessionId），也删除
    return true
  })
  
  // 统计要删除的对话类型
  const syncedButMissing = conversationsToRemove.filter(conv => conv.historySessionId)
  const pureLocalConversations = conversationsToRemove.filter(conv => !conv.historySessionId)
  
  // 统计保留的对话
  const conversationsToKeep = mockLocalConversations.filter(conv => 
    conv.historySessionId && remoteSessionIds.has(conv.historySessionId)
  )
  
  // 统计云端新增的对话
  const newFromCloud = mockRemoteSessions.filter(session => 
    !mockLocalConversations.find(conv => conv.historySessionId === session.id)
  )
  
  console.log('\n📊 同步分析结果:')
  console.log('-'.repeat(40))
  console.log(`🔢 本地对话总数: ${mockLocalConversations.length}`)
  console.log(`☁️ 云端会话总数: ${mockRemoteSessions.length}`)
  
  console.log('\n🗑️ 将被删除的对话:')
  console.log(`   - 云端已删除的同步对话: ${syncedButMissing.length} 个`)
  syncedButMissing.forEach(conv => {
    console.log(`     • ${conv.title} (云端ID: ${conv.historySessionId})`)
  })
  
  console.log(`   - 纯本地对话: ${pureLocalConversations.length} 个`)
  pureLocalConversations.forEach(conv => {
    console.log(`     • ${conv.title}`)
  })
  
  console.log('\n✅ 将被保留的对话:')
  console.log(`   - 云端仍存在的对话: ${conversationsToKeep.length} 个`)
  conversationsToKeep.forEach(conv => {
    console.log(`     • ${conv.title} (云端ID: ${conv.historySessionId})`)
  })
  
  console.log('\n➕ 将从云端新增的对话:')
  console.log(`   - 云端新对话: ${newFromCloud.length} 个`)
  newFromCloud.forEach(session => {
    console.log(`     • ${session.title} (云端ID: ${session.id})`)
  })
  
  // 计算同步后的最终状态
  const finalConversationCount = conversationsToKeep.length + newFromCloud.length
  
  console.log('\n🎯 同步后状态预测:')
  console.log(`   - 最终对话数量: ${finalConversationCount} 个`)
  console.log(`   - 删除总数: ${conversationsToRemove.length} 个`)
  console.log(`   - 新增总数: ${newFromCloud.length} 个`)
  console.log(`   - 保留总数: ${conversationsToKeep.length} 个`)
  
  console.log('\n' + '='.repeat(60))
  console.log('✅ 彻底同步测试完成！')
  
  return {
    original: mockLocalConversations.length,
    cloudSessions: mockRemoteSessions.length,
    toDelete: conversationsToRemove.length,
    syncedButMissing: syncedButMissing.length,
    pureLocal: pureLocalConversations.length,
    toKeep: conversationsToKeep.length,
    newFromCloud: newFromCloud.length,
    finalCount: finalConversationCount
  }
}

/**
 * 在浏览器控制台中运行测试
 */
export function runTestInConsole() {
  if (typeof window !== 'undefined') {
    // @ts-ignore
    window.testThoroughSyncLogic = testThoroughSyncLogic
    console.log('🎯 测试函数已添加到 window.testThoroughSyncLogic')
    console.log('请在控制台中运行: testThoroughSyncLogic()')
  }
}

// 自动运行测试（如果在Node.js环境中）
if (typeof window === 'undefined') {
  testThoroughSyncLogic()
}
