<template>
  <div class="flex h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
    <!-- 知识库列表侧边栏 -->
    <div class="w-72 lg:w-80 xl:w-96 shrink-0 border-r border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm flex flex-col">
      <!-- 头部 -->
      <div class="p-6 border-b border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-xl font-semibold text-slate-900 dark:text-slate-100">
            📚 知识库管理
          </h1>
          <Button
            @click="showCreateDialog = true"
            size="sm"
            class="bg-blue-600 hover:bg-blue-700"
          >
            <Plus class="h-4 w-4 mr-1" />
            新建
          </Button>
        </div>
        
        <!-- 搜索框 -->
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            v-model="knowledgeBaseSearch"
            placeholder="搜索知识库..."
            class="pl-10"
          />
        </div>
      </div>

      <!-- 知识库列表 -->
      <ScrollArea class="flex-1 p-4">
        <div class="space-y-2">
          <!-- 全部文档选项 -->
          <div
            :class="[
              'p-4 rounded-lg cursor-pointer transition-all duration-200 group',
              !selectedKnowledgeBase
                ? 'bg-blue-50 dark:bg-blue-950/30 border-2 border-blue-200 dark:border-blue-800'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-slate-200 dark:border-slate-700'
            ]"
            @click="setSelectedKnowledgeBase(null)"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-500 to-slate-600 flex items-center justify-center shadow-sm">
                <FileText class="h-5 w-5 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                  全部文档
                </h3>
                <p class="text-sm text-slate-500 dark:text-slate-400">
                  {{ allDocuments.length }} 个文档
                </p>
              </div>
            </div>
          </div>

          <!-- 未分类文档 -->
          <div
            v-if="uncategorizedDocuments.length > 0"
            :class="[
              'p-4 rounded-lg cursor-pointer transition-all duration-200 group',
              'hover:bg-orange-50 dark:hover:bg-orange-950/30 border border-orange-200 dark:border-orange-700'
            ]"
            @click="showUncategorized = true"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center shadow-sm">
                <AlertTriangle class="h-5 w-5 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                  未分类文档
                </h3>
                <p class="text-sm text-orange-600 dark:text-orange-400">
                  {{ uncategorizedDocuments.length }} 个文档需要分类
                </p>
              </div>
            </div>
          </div>

          <!-- 知识库列表 -->
          <div
            v-for="kb in filteredKnowledgeBases"
            :key="kb.id"
            :class="[
              'p-4 rounded-lg cursor-pointer transition-all duration-200 group',
              selectedKnowledgeBase?.id === kb.id
                ? 'bg-blue-50 dark:bg-blue-950/30 border-2 border-blue-200 dark:border-blue-800'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-slate-200 dark:border-slate-700'
            ]"
            @click="setSelectedKnowledgeBase(kb)"
          >
            <div class="flex items-center gap-3">
              <!-- 知识库图标 -->
              <div 
                :style="{ backgroundColor: kb.color }"
                class="w-10 h-10 rounded-lg flex items-center justify-center shadow-sm"
              >
                <Database class="h-5 w-5 text-white" />
              </div>
              
              <!-- 知识库信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                    {{ kb.name }}
                  </h3>
                  <Badge v-if="kb.isDefault" variant="secondary" class="text-xs">
                    默认
                  </Badge>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400">
                  {{ knowledgeBaseStats[kb.id]?.totalDocuments || 0 }} 个文档
                  <span v-if="knowledgeBaseStats[kb.id]?.recentlyAdded" class="text-green-600 dark:text-green-400">
                    · {{ knowledgeBaseStats[kb.id].recentlyAdded }} 个新增
                  </span>
                </p>
                <p v-if="kb.description" class="text-xs text-slate-400 dark:text-slate-500 mt-1 truncate">
                  {{ kb.description }}
                </p>
              </div>

              <!-- 操作按钮 -->
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity"
                    @click.stop
                  >
                    <MoreVertical class="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem @click="editKnowledgeBase(kb)">
                    <Edit2 class="h-4 w-4 mr-2" />
                    编辑
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    v-if="!kb.isDefault"
                    @click="confirmDeleteKnowledgeBase(kb)"
                    class="text-red-600 focus:text-red-600"
                  >
                    <Trash2 class="h-4 w-4 mr-2" />
                    删除
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>

    <!-- 主内容区域 -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 工具栏 -->
      <div class="p-4 lg:p-6 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div class="flex items-center gap-4 min-w-0">
            <div class="min-w-0 flex-1">
              <h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100 truncate">
                {{ selectedKnowledgeBase ? selectedKnowledgeBase.name : '全部文档' }}
              </h2>
              <p class="text-sm text-slate-500 dark:text-slate-400">
                {{ enhancedFilteredDocuments.length }} 个文档
                <span v-if="selectedDocuments.size > 0" class="text-purple-600 dark:text-purple-400">
                  · 已选择 {{ selectedDocuments.size }} 个
                </span>
              </p>
            </div>
            
            <!-- 快速统计 -->
            <div v-if="selectedKnowledgeBase && knowledgeBaseStats[selectedKnowledgeBase.id]" class="hidden xl:flex items-center gap-4 text-sm text-slate-500">
              <span class="flex items-center gap-1 whitespace-nowrap">
                <Hash class="h-4 w-4" />
                {{ knowledgeBaseStats[selectedKnowledgeBase.id].totalChunks }} 个片段
              </span>
              <span class="flex items-center gap-1 whitespace-nowrap">
                <HardDrive class="h-4 w-4" />
                {{ formatFileSize(knowledgeBaseStats[selectedKnowledgeBase.id].totalSize) }}
              </span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 min-w-0">
            <!-- 文档上传（仅在选择知识库时显示） -->
            <div v-if="selectedKnowledgeBase" class="flex items-center gap-2">
              <input
                ref="fileInputRef"
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.txt,.doc,.docx"
                class="hidden"
                @change="handleFileSelect"
              />
              <Button
                @click="triggerFileUpload"
                :disabled="isUploading"
                variant="default"
                size="sm"
                class="bg-green-600 hover:bg-green-700 whitespace-nowrap"
              >
                <template v-if="isUploading">
                  <Loader2 class="h-4 w-4 animate-spin mr-1" />
                  上传中...
                </template>
                <template v-else>
                  <Upload class="h-4 w-4 mr-1" />
                  上传文档
                </template>
              </Button>
              
              <!-- 上传进度提示 -->
              <div v-if="uploadProgress.length > 0" class="text-sm">
                <Badge variant="secondary" class="whitespace-nowrap">
                  {{ uploadProgress.filter(p => p.completed).length }}/{{ uploadProgress.length }} 完成
                </Badge>
              </div>
            </div>

            <!-- 搜索和过滤 -->
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2" v-if="selectedDocuments.size <= 0">
              <!-- 搜索类型切换 -->
              <div class="flex items-center gap-1 border border-slate-200 dark:border-slate-700 rounded-lg p-1 shrink-0">
                <Button
                  @click="searchType = 'filename'"
                  :variant="searchType === 'filename' ? 'default' : 'ghost'"
                  size="sm"
                  class="h-8 px-2 lg:px-3 text-xs"
                >
                  <FileText class="h-3 w-3 mr-1" />
                  <span class="hidden sm:inline">文档名</span>
                </Button>
                <Button
                  @click="searchType = 'content'"
                  :variant="searchType === 'content' ? 'default' : 'ghost'"
                  size="sm"
                  class="h-8 px-2 lg:px-3 text-xs"
                >
                  <Search class="h-3 w-3 mr-1" />
                  <span class="hidden sm:inline">内容</span>
                </Button>
              </div>
              
              <!-- 搜索框 -->
              <div class="relative flex-1 min-w-0">
                <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  v-model="documentSearch"
                  :placeholder="searchType === 'filename' ? '搜索文档名...' : '搜索文档内容...'"
                  class="pl-10 w-full"
                  @keydown.enter="handleSearch"
                />
                <Button
                  v-if="documentSearch && searchType === 'content'"
                  @click="handleSearch"
                  :disabled="isSearching"
                  variant="ghost"
                  size="sm"
                  class="absolute right-1 top-1/2 transform -translate-y-1/2 h-7 px-2"
                >
                  <template v-if="isSearching">
                    <Loader2 class="h-3 w-3 animate-spin" />
                  </template>
                  <template v-else>
                    检索
                  </template>
                </Button>
              </div>
              
              <Button
                @click="showFilterDialog = true"
                variant="outline"
                size="sm"
                class="shrink-0"
              >
                <Filter class="h-4 w-4 mr-1" />
                <span class="hidden sm:inline">筛选</span>
              </Button>
            </div>

            <!-- 批量操作 -->
            <div v-if="selectedDocuments.size > 0" class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <Select v-model="batchMoveTarget" @update:model-value="(value: any) => value && typeof value === 'string' && handleBatchMove(value)">
                <SelectTrigger class="w-full sm:w-48">
                  <SelectValue placeholder="移动到知识库..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem
                    v-for="kb in knowledgeBases"
                    :key="kb.id"
                    :value="kb.id"
                  >
                    {{ kb.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
              
              <Button
                @click="handleBatchDelete"
                variant="destructive"
                size="sm"
                class="whitespace-nowrap"
              >
                <Trash2 class="h-4 w-4 mr-1" />
                <span class="hidden sm:inline">删除</span>
              </Button>
            </div>

            <Button
              @click="refreshDocuments"
              :disabled="isLoading"
              variant="outline"
              size="sm"
              class="shrink-0"
            >
              <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
            </Button>
          </div>
        </div>
      </div>

      <!-- 搜索状态提示 -->
      <div v-if="searchType === 'content' && (isSearching || semanticSearchResults)" class="px-4 lg:px-6 py-3 bg-blue-50 dark:bg-blue-950/30 border-b border-blue-200 dark:border-blue-800">
        <div v-if="isSearching" class="flex items-center gap-2 text-blue-600 dark:text-blue-400">
          <Loader2 class="h-4 w-4 animate-spin" />
          <span class="text-sm">正在检索"{{ documentSearch }}"的相关内容...</span>
        </div>
        <div v-else-if="semanticSearchResults" class="text-sm">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-blue-600 dark:text-blue-400">
              <span class="flex items-center gap-1 whitespace-nowrap">
                🔍 找到 {{ semanticSearchResults.chunks.length }} 个相关片段
              </span>
              <span class="flex items-center gap-1 whitespace-nowrap">
                📄 涉及 {{ searchedDocIds.size }} 个文档
              </span>
              <span class="text-xs text-slate-500 whitespace-nowrap">
                耗时 {{ semanticSearchResults.search_time.toFixed(2) }}s
              </span>
            </div>
            <Button
              @click="clearSemanticSearch"
              variant="ghost"
              size="sm"
              class="text-xs shrink-0 self-start sm:self-auto"
            >
              <X class="h-3 w-3 mr-1" />
              清除检索
            </Button>
          </div>
          <div v-if="semanticSearchResults.chunks.length === 0" class="text-amber-600 dark:text-amber-400 mt-1">
            💡 未找到相关内容，请尝试调整搜索关键词
          </div>
        </div>
      </div>

      <!-- 文档列表 -->
      <ScrollArea class="flex-1 p-6">
        <div v-if="isLoading && !hasDocuments" class="flex flex-col items-center justify-center py-20">
          <Loader2 class="h-12 w-12 animate-spin text-slate-400 mb-4" />
          <p class="text-slate-500">正在加载文档...</p>
        </div>

        <div v-else-if="!hasDocuments" class="flex flex-col items-center justify-center py-20">
          <FileText class="h-20 w-20 text-slate-300 dark:text-slate-600 mb-6" />
          <h3 class="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
            {{ selectedKnowledgeBase ? '该知识库还没有文档' : '还没有任何文档' }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">
            在聊天界面上传文件即可自动添加到知识库
          </p>
        </div>

        <div v-else-if="enhancedFilteredDocuments.length === 0" class="flex flex-col items-center justify-center py-20">
          <Search class="h-20 w-20 text-slate-300 dark:text-slate-600 mb-6" />
          <h3 class="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
            {{ searchType === 'content' ? '未找到相关内容' : '未找到匹配的文档' }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">
            {{ searchType === 'content' 
              ? '尝试使用不同的关键词或降低搜索精度' 
              : '尝试修改搜索条件或清除筛选' 
            }}
          </p>
          <div v-if="searchType === 'content'" class="text-xs text-slate-400 space-y-1">
            <p>💡 搜索建议：</p>
            <p>• 使用更通用的关键词</p>
            <p>• 尝试相关的同义词</p>
            <p>• 检查拼写是否正确</p>
          </div>
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
          <div
            v-for="document in enhancedFilteredDocuments"
            :key="document.doc_id"
            :class="[
              'group p-4 rounded-lg border cursor-pointer transition-all duration-200',
              selectedDocuments.has(document.doc_id)
                ? 'border-purple-300 bg-purple-50 dark:border-purple-700 dark:bg-purple-950/30 shadow-md transform scale-105'
                : 'border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50 hover:shadow-lg'
            ]"
            @click="toggleDocument(document.doc_id)"
          >
            <!-- 选择指示器 -->
            <div class="flex items-start justify-between mb-3">
              <div
                :class="[
                  'w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200',
                  selectedDocuments.has(document.doc_id)
                    ? 'border-purple-500 bg-purple-500 scale-110'
                    : 'border-slate-300 dark:border-slate-600 group-hover:border-purple-400'
                ]"
              >
                <Check v-if="selectedDocuments.has(document.doc_id)" class="h-3 w-3 text-white" />
              </div>
              
              <!-- 文档操作 -->
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-7 w-7"
                    @click.stop
                  >
                    <MoreVertical class="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem @click="previewDocument(document)">
                    <Eye class="h-4 w-4 mr-2" />
                    预览
                  </DropdownMenuItem>
                  <DropdownMenuItem @click="showMoveDialog(document)">
                    <Folder class="h-4 w-4 mr-2" />
                    移动
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    @click="deleteDocument(document.doc_id)"
                    class="text-red-600 focus:text-red-600"
                  >
                    <Trash2 class="h-4 w-4 mr-2" />
                    删除
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <!-- 文档信息 -->
            <div class="space-y-3">
              <!-- 文件图标和类型 -->
              <div class="flex items-center gap-2">
                <FileText class="h-8 w-8 text-blue-500" />
                <Badge variant="outline" class="text-xs">
                  {{ getFileTypeDisplay(document.file_type) }}
                </Badge>
              </div>

              <!-- 文件名 -->
              <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate" :title="document.filename">
                {{ document.filename }}
              </h3>

              <!-- 统计信息 -->
              <div class="space-y-1 text-xs text-slate-500 dark:text-slate-400">
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1">
                    <Hash class="h-3 w-3" />
                    {{ document.chunk_count }} 片段
                  </span>
                  <span>{{ formatFileSize(document.total_length) }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ formatDate(document.created_at) }}
                </div>
              </div>

              <!-- 相关度显示（仅在语义搜索时显示） -->
              <div v-if="searchType === 'content' && semanticSearchResults && getDocumentRelevance(document.doc_id)" class="mt-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-green-600 dark:text-green-400 font-medium">
                    🎯 相关度: {{ (getDocumentRelevance(document.doc_id)!.maxSimilarity * 100).toFixed(1) }}%
                  </span>
                  <span class="text-slate-500">
                    {{ getDocumentRelevance(document.doc_id)!.chunkCount }} 个相关片段
                  </span>
                </div>
                <div class="mt-1 w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1">
                  <div 
                    class="bg-green-500 h-1 rounded-full transition-all duration-300"
                    :style="{ width: `${getDocumentRelevance(document.doc_id)!.maxSimilarity * 100}%` }"
                  ></div>
                </div>
              </div>

              <!-- 所属知识库 -->
              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="kb in getDocumentKnowledgeBases(document.doc_id)"
                  :key="kb.id"
                  variant="secondary"
                  class="text-xs px-1.5 py-0.5"
                  :style="{ backgroundColor: `${kb.color}20`, borderColor: kb.color }"
                >
                  {{ kb.name }}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  </div>

  <!-- 创建知识库对话框 -->
  <Dialog v-model:open="showCreateDialog">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ editingKnowledgeBase ? '编辑知识库' : '创建新知识库' }}</DialogTitle>
        <DialogDescription>
          {{ editingKnowledgeBase ? '修改知识库信息' : '创建一个新的知识库来组织你的文档' }}
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-4">
        <div>
          <Label for="kb-name">知识库名称</Label>
          <Input
            id="kb-name"
            v-model="newKnowledgeBase.name"
            placeholder="输入知识库名称"
            class="mt-1"
          />
        </div>
        
        <div>
          <Label for="kb-description">描述（可选）</Label>
          <Textarea
            id="kb-description"
            v-model="newKnowledgeBase.description"
            placeholder="简单描述这个知识库的用途"
            class="mt-1"
            rows="3"
          />
        </div>
        
        <div>
          <Label>颜色</Label>
          <div class="flex gap-2 mt-2">
            <button
              v-for="color in availableColors"
              :key="color"
              :style="{ backgroundColor: color }"
              :class="[
                'w-8 h-8 rounded-lg border-2 transition-all duration-200',
                newKnowledgeBase.color === color
                  ? 'border-slate-900 dark:border-white scale-110'
                  : 'border-slate-300 dark:border-slate-600 hover:scale-105'
              ]"
              @click="newKnowledgeBase.color = color"
            />
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <Button variant="outline" @click="showCreateDialog = false">
          取消
        </Button>
        <Button @click="handleCreateKnowledgeBase">
          {{ editingKnowledgeBase ? '保存' : '创建' }}
        </Button>
      </div>
    </DialogContent>
  </Dialog>

  <!-- 未分类文档对话框 -->
  <Dialog v-model:open="showUncategorized">
    <DialogContent class="max-w-4xl max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>未分类文档</DialogTitle>
        <DialogDescription>
          以下文档还未添加到任何知识库，建议将它们分类整理
        </DialogDescription>
      </DialogHeader>
      
      <ScrollArea class="flex-1 mt-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="document in uncategorizedDocuments"
            :key="document.doc_id"
            class="p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
          >
            <div class="flex items-center gap-2 mb-2">
              <FileText class="h-5 w-5 text-blue-500" />
              <span class="text-sm font-medium truncate">{{ document.filename }}</span>
            </div>
            <div class="text-xs text-slate-500 mb-3">
              {{ document.chunk_count }} 片段 · {{ formatFileSize(document.total_length) }}
            </div>
            <Select @update:model-value="(value: any) => value && typeof value === 'string' && addToKnowledgeBase(document.doc_id, value)">
              <SelectTrigger class="h-8 text-xs">
                <SelectValue placeholder="选择知识库..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="kb in knowledgeBases"
                  :key="kb.id"
                  :value="kb.id"
                >
                  {{ kb.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </ScrollArea>
    </DialogContent>
  </Dialog>

  <!-- 文档上传进度对话框 -->
  <Dialog v-model:open="showUploadProgress">
    <DialogContent class="sm:max-w-lg">
      <DialogHeader>
        <DialogTitle>文档上传进度</DialogTitle>
        <DialogDescription>
          正在将文档上传到知识库 "{{ selectedKnowledgeBase?.name }}"
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-3 mt-4">
        <div
          v-for="(progress, index) in uploadProgress"
          :key="index"
          class="flex items-center gap-3 p-3 border border-slate-200 dark:border-slate-700 rounded-lg"
        >
          <!-- 状态图标 -->
          <div class="flex-shrink-0">
            <Check v-if="progress.completed && !progress.error" class="h-5 w-5 text-green-600" />
            <AlertTriangle v-else-if="progress.error" class="h-5 w-5 text-red-600" />
            <Loader2 v-else class="h-5 w-5 animate-spin text-blue-600" />
          </div>
          
          <!-- 文件信息 -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
              {{ progress.fileName }}
            </p>
            <p class="text-xs text-slate-500 dark:text-slate-400">
              <span v-if="progress.completed && !progress.error" class="text-green-600">✅ 上传完成</span>
              <span v-else-if="progress.error" class="text-red-600">❌ {{ progress.error }}</span>
              <span v-else class="text-blue-600">🔄 正在上传...</span>
            </p>
          </div>
        </div>
      </div>

      <!-- 整体进度 -->
      <div class="mt-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
        <div class="flex items-center justify-between text-sm">
          <span>整体进度</span>
          <span class="font-medium">
            {{ uploadProgress.filter(p => p.completed).length }}/{{ uploadProgress.length }}
          </span>
        </div>
        <div class="mt-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
          <div 
            class="bg-blue-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${(uploadProgress.filter(p => p.completed).length / uploadProgress.length) * 100}%` }"
          ></div>
        </div>
      </div>

      <div class="flex justify-end mt-6">
        <Button 
          v-if="!isUploading" 
          @click="showUploadProgress = false"
          variant="outline"
        >
          关闭
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Plus,
  Search,
  Database,
  FileText,
  MoreVertical,
  Edit2,
  Trash2,
  Hash,
  Clock,
  Check,
  Eye,
  Folder,
  Filter,
  RefreshCw,
  Loader2,
  AlertTriangle,
  HardDrive,
  Upload,
  X
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { deleteDocument as apiDeleteDocument, uploadFile } from '@/utils/api'
import type { KnowledgeBase, RAGDocument } from '@/types'

// 引入RAG搜索相关API和类型
import { searchDocuments } from '@/utils/api'
import type { RAGSearchRequest, RAGSearchResponse, DocumentChunk } from '@/types'

// Store
const knowledgeBaseStore = useKnowledgeBaseStore()
const {
  knowledgeBases,
  allDocuments,
  selectedKnowledgeBase,
  selectedDocuments,
  isLoading,
  uncategorizedDocuments,
  knowledgeBaseStats,
  filteredDocuments
} = storeToRefs(knowledgeBaseStore)

const {
  initialize,
  fetchAllDocuments,
  setSelectedKnowledgeBase,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  toggleDocument,
  clearSelection,
  updateSearchOptions,
  addDocumentsToKnowledgeBase,
  moveDocuments,
  getDocumentKnowledgeBases,
  formatFileSize,
  formatDate,
  availableColors
} = knowledgeBaseStore

// 本地状态
const knowledgeBaseSearch = ref('')
const documentSearch = ref('')
const showCreateDialog = ref(false)
const showUncategorized = ref(false)
const showFilterDialog = ref(false)
const showUploadProgress = ref(false)
const editingKnowledgeBase = ref<KnowledgeBase | null>(null)
const batchMoveTarget = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const searchType = ref('filename')
const isSearching = ref(false)

// RAG内容搜索相关状态
const semanticSearchResults = ref<RAGSearchResponse | null>(null)
const searchedDocIds = ref<Set<string>>(new Set())
const lastSearchQuery = ref('')

// 定义上传进度类型
interface UploadProgress {
  fileName: string
  completed: boolean
  error?: string
}

const uploadProgress = ref<UploadProgress[]>([])

// 新建/编辑知识库表单
const newKnowledgeBase = ref({
  name: '',
  description: '',
  color: availableColors[0]
})

// 计算属性
const hasDocuments = computed(() => allDocuments.value.length > 0)

const filteredKnowledgeBases = computed(() => {
  if (!knowledgeBaseSearch.value) return knowledgeBases.value
  
  const query = knowledgeBaseSearch.value.toLowerCase()
  return knowledgeBases.value.filter(kb =>
    kb.name.toLowerCase().includes(query) ||
    (kb.description && kb.description.toLowerCase().includes(query))
  )
})

// 监听文档搜索
watch(documentSearch, (value) => {
  if (searchType.value === 'filename') {
    updateSearchOptions({ query: value })
    // 清除语义搜索结果
    if (!value) {
      clearSemanticSearch()
    }
  }
})

// 监听搜索类型切换
watch(searchType, () => {
  clearSemanticSearch()
  if (searchType.value === 'filename') {
    updateSearchOptions({ query: documentSearch.value })
  }
})

// 增强的过滤文档列表计算属性
const enhancedFilteredDocuments = computed(() => {
  if (searchType.value === 'content' && semanticSearchResults.value) {
    // 语义搜索模式：根据相关度排序
    const chunks = semanticSearchResults.value.chunks
    if (chunks.length === 0) return []
    
    // 按文档分组并计算总相关度
    const docScores = new Map<string, { doc: RAGDocument, maxSimilarity: number, totalScore: number, chunkCount: number }>()
    
    chunks.forEach(chunk => {
      const docId = chunk.metadata.doc_id
      const doc = filteredDocuments.value.find(d => d.doc_id === docId)
      if (doc) {
        const existing = docScores.get(docId)
        if (existing) {
          existing.maxSimilarity = Math.max(existing.maxSimilarity, chunk.similarity)
          existing.totalScore += chunk.similarity
          existing.chunkCount += 1
        } else {
          docScores.set(docId, {
            doc,
            maxSimilarity: chunk.similarity,
            totalScore: chunk.similarity,
            chunkCount: 1
          })
        }
      }
    })
    
    // 按平均相关度排序
    return Array.from(docScores.values())
      .sort((a, b) => {
        const avgA = a.totalScore / a.chunkCount
        const avgB = b.totalScore / b.chunkCount
        return avgB - avgA
      })
      .map(item => item.doc)
  }
  
  // 文档名搜索模式或默认模式
  return filteredDocuments.value
})

// 生命周期
onMounted(async () => {
  await initialize()
})

// 文件类型显示
function getFileTypeDisplay(type: string): string {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'image/png': 'PNG',
    'image/jpeg': 'JPG',
    'image/jpg': 'JPG',
    'audio/wav': 'WAV',
    'audio/mp3': 'MP3'
  }
  return typeMap[type] || type.split('/').pop()?.toUpperCase() || '未知'
}

// 刷新文档
async function refreshDocuments() {
  await fetchAllDocuments()
}

// 创建/编辑知识库
function editKnowledgeBase(kb: KnowledgeBase) {
  editingKnowledgeBase.value = kb
  newKnowledgeBase.value = {
    name: kb.name,
    description: kb.description || '',
    color: kb.color || availableColors[0]
  }
  showCreateDialog.value = true
}

async function handleCreateKnowledgeBase() {
  try {
    if (editingKnowledgeBase.value) {
      // 编辑现有知识库
      await updateKnowledgeBase(editingKnowledgeBase.value.id, newKnowledgeBase.value)
    } else {
      // 创建新知识库
      const kb = await createKnowledgeBase(newKnowledgeBase.value)
      setSelectedKnowledgeBase(kb)
    }
    
    // 重置表单
    newKnowledgeBase.value = {
      name: '',
      description: '',
      color: availableColors[0]
    }
    editingKnowledgeBase.value = null
    showCreateDialog.value = false
  } catch (error) {
    console.error('操作失败:', error)
    alert('操作失败，请重试')
  }
}

// 删除知识库
async function confirmDeleteKnowledgeBase(kb: KnowledgeBase) {
  if (confirm(`确定要删除知识库"${kb.name}"吗？删除后无法恢复。`)) {
    await deleteKnowledgeBase(kb.id)
  }
}

// 批量操作
async function handleBatchMove(targetKbId: string) {
  if (!targetKbId || selectedDocuments.value.size === 0) return
  
  try {
    const docIds = Array.from(selectedDocuments.value)
    await moveDocuments(docIds, targetKbId, selectedKnowledgeBase.value?.id)
    clearSelection()
    batchMoveTarget.value = ''
  } catch (error) {
    console.error('移动文档失败:', error)
    alert('移动文档失败，请重试')
  }
}

async function handleBatchDelete() {
  if (selectedDocuments.value.size === 0) return
  
  const count = selectedDocuments.value.size
  if (confirm(`确定要删除选中的 ${count} 个文档吗？删除后无法恢复。`)) {
    try {
      const docIds = Array.from(selectedDocuments.value)
      await Promise.all(docIds.map(docId => apiDeleteDocument(docId)))
      
      // 重新获取文档列表
      await fetchAllDocuments()
      clearSelection()
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除文档失败，请重试')
    }
  }
}

// 文档操作
function previewDocument(document: RAGDocument) {
  // TODO: 实现文档预览功能
  console.log('预览文档:', document.filename)
}

function showMoveDialog(document: RAGDocument) {
  // TODO: 实现文档移动对话框
  console.log('移动文档:', document.filename)
}

async function deleteDocument(docId: string) {
  if (confirm('确定要删除这个文档吗？删除后无法恢复。')) {
    try {
      await apiDeleteDocument(docId)
      await fetchAllDocuments()
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除文档失败，请重试')
    }
  }
}

// 将未分类文档添加到知识库
async function addToKnowledgeBase(docId: string, kbId: string) {
  try {
    await addDocumentsToKnowledgeBase(kbId, [docId])
    // 刷新未分类列表
    await fetchAllDocuments()
  } catch (error) {
    console.error('添加文档到知识库失败:', error)
    alert('添加失败，请重试')
  }
}

// 处理文件上传
function triggerFileUpload() {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target && target.files) {
    const files = Array.from(target.files)
    uploadMultipleFiles(files)
  }
}

async function uploadMultipleFiles(files: File[]) {
  if (!selectedKnowledgeBase.value?.id) {
    alert('请先选择一个知识库')
    return
  }

  isUploading.value = true
  showUploadProgress.value = true
  uploadProgress.value = files.map(file => ({
    fileName: file.name,
    completed: false
  }))

  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      await handleSingleFileUpload(file, i)
    }
    
    // 上传完成后刷新文档列表
    await fetchAllDocuments()
  } catch (error) {
    console.error('批量上传失败:', error)
  } finally {
    isUploading.value = false
    // 延迟关闭对话框，让用户看到完成状态
    setTimeout(() => {
      showUploadProgress.value = false
      uploadProgress.value = []
    }, 3000)
  }
}

async function handleSingleFileUpload(file: File, index: number) {
  try {
    // 使用现有的上传API
    const processedFile = await uploadFile(file)
    
    // 如果文档处理成功并且有doc_id，添加到当前知识库
    if (processedFile.doc_id && selectedKnowledgeBase.value?.id) {
      await addDocumentsToKnowledgeBase(selectedKnowledgeBase.value.id, [processedFile.doc_id])
    }
    
    // 更新进度
    uploadProgress.value[index].completed = true
  } catch (error) {
    console.error(`上传文件 ${file.name} 失败:`, error)
    uploadProgress.value[index].error = error instanceof Error ? error.message : '上传失败'
  }
}

// 处理搜索
async function handleSearch() {
  if (!documentSearch.value.trim()) {
    clearSemanticSearch()
    return
  }

  if (searchType.value === 'filename') {
    updateSearchOptions({ query: documentSearch.value })
    clearSemanticSearch()
  } else if (searchType.value === 'content') {
    await performSemanticSearch(documentSearch.value)
  }
}

// 执行语义搜索
async function performSemanticSearch(query: string) {
  if (!query.trim()) return

  isSearching.value = true
  try {
    // 获取当前知识库的文档ID列表
    let docIds: string[] | undefined
    if (selectedKnowledgeBase.value) {
      docIds = selectedKnowledgeBase.value.documentIds
      if (docIds.length === 0) {
        semanticSearchResults.value = { chunks: [], total_found: 0, search_time: 0 }
        return
      }
    }

    const request: RAGSearchRequest = {
      query,
      doc_ids: docIds,
      top_k: 20, // 增加返回数量以获得更多相关文档
      min_similarity: 0.3 // 降低相似度阈值以获得更多结果
    }

    console.log('🔍 执行知识库内容检索:', {
      query,
      knowledgeBase: selectedKnowledgeBase.value?.name || '全部文档',
      docIds: docIds?.length || '全部'
    })

    const response = await searchDocuments(request)
    semanticSearchResults.value = response
    lastSearchQuery.value = query

    // 记录搜索到的文档ID
    searchedDocIds.value.clear()
    response.chunks.forEach(chunk => {
      searchedDocIds.value.add(chunk.metadata.doc_id)
    })

    console.log('✅ 语义搜索完成:', {
      chunksFound: response.chunks.length,
      documentsFound: searchedDocIds.value.size,
      searchTime: response.search_time.toFixed(3) + 's'
    })

  } catch (error) {
    console.error('❌ 语义搜索失败:', error)
    semanticSearchResults.value = { chunks: [], total_found: 0, search_time: 0 }
  } finally {
    isSearching.value = false
  }
}

// 清除语义搜索结果
function clearSemanticSearch() {
  semanticSearchResults.value = null
  searchedDocIds.value.clear()
  lastSearchQuery.value = ''
}

// 获取文档相关度
function getDocumentRelevance(docId: string) {
  if (searchType.value === 'content' && semanticSearchResults.value) {
    const chunks = semanticSearchResults.value.chunks.filter(c => c.metadata.doc_id === docId)
    if (chunks.length > 0) {
      const maxSimilarity = Math.max(...chunks.map(c => c.similarity))
      return {
        maxSimilarity,
        chunkCount: chunks.length
      }
    }
  }
  return null
}
</script> 