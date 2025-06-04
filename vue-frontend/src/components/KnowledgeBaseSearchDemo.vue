<template>
  <div class="p-6 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
    <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
      🔍 知识库内容检索功能演示
    </h3>
    
    <div class="space-y-4">
      <div class="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg">
        <h4 class="font-medium text-blue-900 dark:text-blue-100 mb-2">新功能亮点</h4>
        <ul class="text-sm text-blue-700 dark:text-blue-300 space-y-1">
          <li>✅ 支持文档名搜索和内容语义搜索</li>
          <li>✅ 智能相关度排序，最相关的文档排在前面</li>
          <li>✅ 显示文档相关度评分和相关片段数量</li>
          <li>✅ 支持知识库范围内的精准检索</li>
          <li>✅ 实时搜索状态和结果统计</li>
        </ul>
      </div>
      
      <div class="bg-green-50 dark:bg-green-950/30 p-4 rounded-lg">
        <h4 class="font-medium text-green-900 dark:text-green-100 mb-2">使用方法</h4>
        <ol class="text-sm text-green-700 dark:text-green-300 space-y-1">
          <li>1. 进入知识库管理页面</li>
          <li>2. 选择搜索类型：文档名 或 内容</li>
          <li>3. 输入搜索关键词</li>
          <li>4. 按回车或点击"检索"按钮</li>
          <li>5. 查看相关度排序的文档结果</li>
        </ol>
      </div>
      
      <div class="bg-amber-50 dark:bg-amber-950/30 p-4 rounded-lg">
        <h4 class="font-medium text-amber-900 dark:text-amber-100 mb-2">搜索技巧</h4>
        <ul class="text-sm text-amber-700 dark:text-amber-300 space-y-1">
          <li>💡 使用具体的关键词获得更精准的结果</li>
          <li>💡 尝试不同的同义词扩大搜索范围</li>
          <li>💡 内容搜索支持语义理解，无需完全匹配</li>
          <li>💡 相关度评分帮助您快速找到最相关的文档</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 这是一个纯展示组件，无需额外逻辑
</script> 