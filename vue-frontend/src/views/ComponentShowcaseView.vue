<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 p-6">
    <div class="container mx-auto max-w-7xl">
      <div class="space-y-8">
        <!-- 页面标题 -->
        <div class="text-center">
          <h1 class="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            小智小智 -Vue 组件库
          </h1>
          <p class="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            完整的现代化UI组件展示，用于构建美观、交互丰富的Vue应用程序
          </p>
        </div>

        <!-- 导航标签 -->
        <div class="flex justify-center">
          <Tabs v-model="activeTab" class="w-full max-w-7xl">
            <TabsList class="grid w-full grid-cols-6">
              <TabsTrigger value="basic">基础组件</TabsTrigger>
              <TabsTrigger value="form">表单组件</TabsTrigger>
              <TabsTrigger value="layout">布局组件</TabsTrigger>
              <TabsTrigger value="feedback">反馈组件</TabsTrigger>
              <TabsTrigger value="navigation">导航组件</TabsTrigger>
              <TabsTrigger value="advanced">高级组件</TabsTrigger>
            </TabsList>

            <!-- 基础组件 -->
            <TabsContent value="basic" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- 按钮组件 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <MousePointer class="h-5 w-5 text-blue-500" />
                      Button 按钮
                    </CardTitle>
                    <CardDescription>各种样式和尺寸的按钮组件</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex flex-wrap gap-2">
                      <Button variant="default">默认</Button>
                      <Button variant="secondary">次要</Button>
                      <Button variant="destructive">危险</Button>
                      <Button variant="outline">轮廓</Button>
                      <Button variant="ghost">幽灵</Button>
                      <Button variant="link">链接</Button>
                    </div>
                    <div class="flex items-center gap-2">
                      <Button size="sm">小</Button>
                      <Button size="default">默认</Button>
                      <Button size="lg">大</Button>
                      <Button size="icon" class="rounded-full">
                        <Star class="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <!-- 徽章组件 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Tag class="h-5 w-5 text-green-500" />
                      Badge 徽章
                    </CardTitle>
                    <CardDescription>用于显示状态和分类的标签</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex flex-wrap gap-2">
                      <Badge variant="default">默认</Badge>
                      <Badge variant="secondary">次要</Badge>
                      <Badge variant="destructive">错误</Badge>
                      <Badge variant="outline">轮廓</Badge>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <Badge class="bg-green-500">在线</Badge>
                      <Badge class="bg-yellow-500">处理中</Badge>
                      <Badge class="bg-red-500">离线</Badge>
                      <Badge class="bg-blue-500">连接中</Badge>
                    </div>
                  </CardContent>
                </Card>

                <!-- 头像组件 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <User class="h-5 w-5 text-purple-500" />
                      Avatar 头像
                    </CardTitle>
                    <CardDescription>用户头像和图标显示</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex items-center gap-4">
                      <Avatar class="w-8 h-8">
                        <AvatarFallback class="bg-blue-500 text-white text-xs">U</AvatarFallback>
                      </Avatar>
                      <Avatar class="w-12 h-12">
                        <AvatarFallback class="bg-green-500 text-white">
                          <User class="h-6 w-6" />
                        </AvatarFallback>
                      </Avatar>
                      <Avatar class="w-16 h-16">
                        <AvatarFallback class="bg-purple-500 text-white">
                          <Bot class="h-8 w-8" />
                        </AvatarFallback>
                      </Avatar>
                    </div>
                  </CardContent>
                </Card>

                <!-- 开关组件 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ToggleLeft class="h-5 w-5 text-orange-500" />
                      Switch 开关
                    </CardTitle>
                    <CardDescription>开关和切换控件</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex items-center space-x-2">
                      <Switch v-model:checked="switch1" />
                      <Label>启用通知</Label>
                    </div>
                    <div class="flex items-center space-x-2">
                      <Switch v-model:checked="switch2" />
                      <Label>暗色模式</Label>
                    </div>
                    <div class="flex items-center space-x-2">
                      <Switch v-model:checked="switch3" disabled />
                      <Label>禁用选项</Label>
                    </div>
                  </CardContent>
                </Card>

                <!-- 切换按钮 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ToggleRight class="h-5 w-5 text-teal-500" />
                      Toggle 切换
                    </CardTitle>
                    <CardDescription>可切换状态的按钮</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex gap-2">
                      <Toggle v-model:pressed="toggle1" aria-label="粗体">
                        <Bold class="h-4 w-4" />
                      </Toggle>
                      <Toggle v-model:pressed="toggle2" aria-label="斜体">
                        <Italic class="h-4 w-4" />
                      </Toggle>
                      <Toggle v-model:pressed="toggle3" aria-label="下划线">
                        <Underline class="h-4 w-4" />
                      </Toggle>
                    </div>
                    <ToggleGroup v-model="toggleGroup" type="multiple">
                      <ToggleGroupItem value="bold" aria-label="粗体">
                        <Bold class="h-4 w-4" />
                      </ToggleGroupItem>
                      <ToggleGroupItem value="italic" aria-label="斜体">
                        <Italic class="h-4 w-4" />
                      </ToggleGroupItem>
                      <ToggleGroupItem value="underline" aria-label="下划线">
                        <Underline class="h-4 w-4" />
                      </ToggleGroupItem>
                    </ToggleGroup>
                  </CardContent>
                </Card>

                <!-- 滑块组件 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <SlidersHorizontal class="h-5 w-5 text-pink-500" />
                      Slider 滑块
                    </CardTitle>
                    <CardDescription>数值选择滑块</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <Label>音量: {{ sliderValue1 }}%</Label>
                      <Slider v-model="sliderValue1" :max="100" :step="1" />
                    </div>
                    <div class="space-y-2">
                      <Label>范围: {{ sliderValue2[0] }} - {{ sliderValue2[1] }}</Label>
                      <Slider v-model="sliderValue2" :max="100" :step="1" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <!-- 表单组件 -->
            <TabsContent value="form" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- 输入框 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Type class="h-5 w-5 text-blue-500" />
                      Input 输入框
                    </CardTitle>
                    <CardDescription>各种类型的输入组件</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <Label>用户名</Label>
                      <Input v-model="inputValue1" placeholder="请输入用户名" />
                    </div>
                    <div class="space-y-2">
                      <Label>密码</Label>
                      <Input v-model="inputValue2" type="password" placeholder="请输入密码" />
                    </div>
                    <div class="space-y-2">
                      <Label>邮箱</Label>
                      <Input v-model="inputValue3" type="email" placeholder="example@domain.com" />
                    </div>
                  </CardContent>
                </Card>

                <!-- 文本域 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <AlignLeft class="h-5 w-5 text-green-500" />
                      Textarea 文本域
                    </CardTitle>
                    <CardDescription>多行文本输入</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <Label>描述</Label>
                      <Textarea 
                        v-model="textareaValue" 
                        placeholder="请输入详细描述..."
                        rows="4"
                      />
                    </div>
                  </CardContent>
                </Card>

                <!-- 选择器 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ChevronDown class="h-5 w-5 text-purple-500" />
                      Select 选择器
                    </CardTitle>
                    <CardDescription>下拉选择组件</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <Label>主题</Label>
                      <Select v-model="selectValue">
                        <SelectTrigger>
                          <SelectValue placeholder="选择主题" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="light">浅色主题</SelectItem>
                          <SelectItem value="dark">深色主题</SelectItem>
                          <SelectItem value="system">跟随系统</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>

                <!-- 复选框 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <CheckSquare class="h-5 w-5 text-orange-500" />
                      Checkbox 复选框
                    </CardTitle>
                    <CardDescription>多选和单选控件</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex items-center space-x-2">
                      <Checkbox v-model:checked="checkbox1" id="checkbox1" />
                      <Label for="checkbox1">接受服务条款</Label>
                    </div>
                    <div class="flex items-center space-x-2">
                      <Checkbox v-model:checked="checkbox2" id="checkbox2" />
                      <Label for="checkbox2">订阅邮件通知</Label>
                    </div>
                    <div class="flex items-center space-x-2">
                      <Checkbox v-model:checked="checkbox3" id="checkbox3" disabled />
                      <Label for="checkbox3">禁用选项</Label>
                    </div>
                  </CardContent>
                </Card>

                <!-- 单选按钮 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Circle class="h-5 w-5 text-teal-500" />
                      RadioGroup 单选
                    </CardTitle>
                    <CardDescription>单选按钮组</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <RadioGroup v-model="radioValue">
                      <div class="flex items-center space-x-2">
                        <RadioGroupItem value="option1" id="option1" />
                        <Label for="option1">选项 1</Label>
                      </div>
                      <div class="flex items-center space-x-2">
                        <RadioGroupItem value="option2" id="option2" />
                        <Label for="option2">选项 2</Label>
                      </div>
                      <div class="flex items-center space-x-2">
                        <RadioGroupItem value="option3" id="option3" />
                        <Label for="option3">选项 3</Label>
                      </div>
                    </RadioGroup>
                  </CardContent>
                </Card>

                <!-- 进度条展示 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <BarChart3 class="h-5 w-5 text-blue-500" />
                      Progress 进度条
                    </CardTitle>
                    <CardDescription>进度指示器</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <div class="flex justify-between text-sm">
                        <span>上传进度</span>
                        <span>{{ progressValue }}%</span>
                      </div>
                      <Progress :value="progressValue" />
                    </div>
                    <Button @click="simulateProgress" size="sm">
                      模拟进度
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <!-- 布局组件 -->
            <TabsContent value="layout" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- 卡片 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Square class="h-5 w-5 text-blue-500" />
                      Card 卡片
                    </CardTitle>
                    <CardDescription>内容容器组件</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <Card class="p-4">
                      <h4 class="font-semibold mb-2">嵌套卡片</h4>
                      <p class="text-sm text-gray-600">这是一个嵌套在主卡片内的子卡片。</p>
                    </Card>
                  </CardContent>
                  <CardFooter>
                    <Button variant="outline" class="w-full">操作按钮</Button>
                  </CardFooter>
                </Card>

                <!-- 分隔符 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Minus class="h-5 w-5 text-green-500" />
                      Separator 分隔符
                    </CardTitle>
                    <CardDescription>内容分隔线</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div>内容区域 1</div>
                    <Separator />
                    <div>内容区域 2</div>
                    <div class="flex items-center gap-4">
                      <span>垂直分隔符</span>
                      <Separator orientation="vertical" class="h-4" />
                      <span>内容区域 3</span>
                    </div>
                  </CardContent>
                </Card>

                <!-- 滚动区域 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ScrollText class="h-5 w-5 text-purple-500" />
                      ScrollArea 滚动
                    </CardTitle>
                    <CardDescription>可滚动内容区域</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea class="h-32 w-full border rounded">
                      <div class="p-4 space-y-2">
                        <div v-for="i in 20" :key="i" class="text-sm">
                          列表项 {{ i }}
                        </div>
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>

                <!-- 手风琴 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ChevronDown class="h-5 w-5 text-orange-500" />
                      Accordion 手风琴
                    </CardTitle>
                    <CardDescription>可折叠内容面板</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible>
                      <AccordionItem value="item-1">
                        <AccordionTrigger>功能特性</AccordionTrigger>
                        <AccordionContent>
                          这是一个现代化的UI组件库，提供丰富的交互组件。
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="item-2">
                        <AccordionTrigger>技术栈</AccordionTrigger>
                        <AccordionContent>
                          基于Vue 3、TypeScript和Tailwind CSS构建。
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </CardContent>
                </Card>

                <!-- 标签页 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Layers class="h-5 w-5 text-teal-500" />
                      Tabs 标签页
                    </CardTitle>
                    <CardDescription>选项卡切换组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Tabs v-model="demoTabValue" class="w-full">
                      <TabsList class="grid w-full grid-cols-2">
                        <TabsTrigger value="tab1">标签1</TabsTrigger>
                        <TabsTrigger value="tab2">标签2</TabsTrigger>
                      </TabsList>
                      <TabsContent value="tab1" class="mt-4">
                        <p class="text-sm">这是第一个标签页的内容。</p>
                      </TabsContent>
                      <TabsContent value="tab2" class="mt-4">
                        <p class="text-sm">这是第二个标签页的内容。</p>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>

                <!-- 面包屑 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Navigation class="h-5 w-5 text-pink-500" />
                      Breadcrumb 面包屑
                    </CardTitle>
                    <CardDescription>导航路径指示</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Breadcrumb>
                      <BreadcrumbList>
                        <BreadcrumbItem>
                          <BreadcrumbLink href="/">首页</BreadcrumbLink>
                        </BreadcrumbItem>
                        <BreadcrumbSeparator />
                        <BreadcrumbItem>
                          <BreadcrumbLink href="/components">组件</BreadcrumbLink>
                        </BreadcrumbItem>
                        <BreadcrumbSeparator />
                        <BreadcrumbItem>
                          <BreadcrumbPage>展示</BreadcrumbPage>
                        </BreadcrumbItem>
                      </BreadcrumbList>
                    </Breadcrumb>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <!-- 反馈组件 -->
            <TabsContent value="feedback" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- 警告 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <AlertTriangle class="h-5 w-5 text-red-500" />
                      Alert 警告
                    </CardTitle>
                    <CardDescription>重要信息提示</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <Alert>
                      <Info class="h-4 w-4" />
                      <AlertTitle>提示</AlertTitle>
                      <AlertDescription>
                        这是一个信息提示。
                      </AlertDescription>
                    </Alert>
                    <Alert variant="destructive">
                      <AlertTriangle class="h-4 w-4" />
                      <AlertTitle>错误</AlertTitle>
                      <AlertDescription>
                        发生了一个错误，请检查输入。
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                </Card>

                <!-- 骨架屏 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Loader2 class="h-5 w-5 text-gray-500" />
                      Skeleton 骨架屏
                    </CardTitle>
                    <CardDescription>加载状态占位</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <Skeleton class="h-4 w-3/4" />
                      <Skeleton class="h-4 w-1/2" />
                      <Skeleton class="h-8 w-full" />
                    </div>
                    <div class="flex items-center space-x-4">
                      <Skeleton class="h-12 w-12 rounded-full" />
                      <div class="space-y-2">
                        <Skeleton class="h-4 w-24" />
                        <Skeleton class="h-4 w-20" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <!-- 对话框 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <MessageSquare class="h-5 w-5 text-green-500" />
                      Dialog 对话框
                    </CardTitle>
                    <CardDescription>模态对话框</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <Dialog v-model:open="dialogOpen">
                      <DialogTrigger as-child>
                        <Button variant="outline">打开对话框</Button>
                      </DialogTrigger>
                      <DialogContent class="sm:max-w-md">
                        <DialogHeader>
                          <DialogTitle>分享链接</DialogTitle>
                          <DialogDescription>
                            任何拥有此链接的人都可以查看此内容。
                          </DialogDescription>
                        </DialogHeader>
                        <div class="flex items-center space-x-2 white">
                          <div class="grid flex-1 gap-2 white">
                            <Label for="link" class="sr-only">链接</Label>
                            <Input
                              id="link"
                              value="https://shadcn-vue.com/docs/installation"
                            />
                          </div>
                          <Button type="submit" size="sm" class="px-3">
                            <Copy class="h-4 w-4" />
                          </Button>
                        </div>
                        <DialogFooter class="sm:justify-start">
                          <DialogClose as-child>
                            <Button type="button" variant="secondary">
                              关闭
                            </Button>
                          </DialogClose>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </CardContent>
                </Card>

                <!-- 悬停卡片 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <MousePointer class="h-5 w-5 text-purple-500" />
                      HoverCard 悬停卡片
                    </CardTitle>
                    <CardDescription>悬停显示详细信息</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <HoverCard>
                      <HoverCardTrigger as-child>
                        <Button variant="link">@username</Button>
                      </HoverCardTrigger>
                      <HoverCardContent class="w-80">
                        <div class="flex justify-between space-x-4">
                          <Avatar>
                            <AvatarFallback>UN</AvatarFallback>
                          </Avatar>
                          <div class="space-y-1">
                            <h4 class="text-sm font-semibold">@username</h4>
                            <p class="text-sm">
                              这是用户的简介信息。
                            </p>
                            <div class="flex items-center pt-2">
                              <Calendar class="mr-2 h-4 w-4 opacity-70" />
                              <span class="text-xs text-muted-foreground">
                                加入于 2023年12月
                              </span>
                            </div>
                          </div>
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                  </CardContent>
                </Card>

                <!-- 工具提示 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <HelpCircle class="h-5 w-5 text-orange-500" />
                      Tooltip 工具提示
                    </CardTitle>
                    <CardDescription>快速信息提示</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="flex gap-4">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger as-child>
                            <Button variant="outline" size="icon">
                              <Plus class="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>添加新项目</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger as-child>
                            <Button variant="outline" size="icon">
                              <Settings class="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>设置选项</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </CardContent>
                </Card>

                <!-- 弹出框 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <MessageCircle class="h-5 w-5 text-teal-500" />
                      Popover 弹出框
                    </CardTitle>
                    <CardDescription>可定位的弹出内容</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Popover>
                      <PopoverTrigger as-child>
                        <Button variant="outline">打开弹出框</Button>
                      </PopoverTrigger>
                      <PopoverContent class="w-80">
                        <div class="grid gap-4">
                          <div class="space-y-2">
                            <h4 class="font-medium leading-none">维度</h4>
                            <p class="text-sm text-muted-foreground">
                              设置组件的尺寸。
                            </p>
                          </div>
                          <div class="grid gap-2">
                            <div class="grid grid-cols-3 items-center gap-4">
                              <Label htmlFor="width">宽度</Label>
                              <Input
                                id="width"
                                defaultValue="100%"
                                className="col-span-2 h-8"
                              />
                            </div>
                            <div class="grid grid-cols-3 items-center gap-4">
                              <Label htmlFor="height">高度</Label>
                              <Input
                                id="height"
                                defaultValue="25px"
                                className="col-span-2 h-8"
                              />
                            </div>
                          </div>
                        </div>
                      </PopoverContent>
                    </Popover>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <!-- 导航组件 -->
            <TabsContent value="navigation" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- 导航菜单 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Navigation class="h-5 w-5 text-blue-500" />
                      NavigationMenu 导航菜单
                    </CardTitle>
                    <CardDescription>响应式导航菜单组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <NavigationMenu>
                      <NavigationMenuList>
                        <NavigationMenuItem>
                          <NavigationMenuTrigger>产品</NavigationMenuTrigger>
                          <NavigationMenuContent>
                            <NavigationMenuLink href="/products">
                              所有产品
                            </NavigationMenuLink>
                          </NavigationMenuContent>
                        </NavigationMenuItem>
                        <NavigationMenuItem>
                          <NavigationMenuLink href="/about">
                            关于我们
                          </NavigationMenuLink>
                        </NavigationMenuItem>
                      </NavigationMenuList>
                    </NavigationMenu>
                  </CardContent>
                </Card>

                <!-- 菜单栏 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Settings class="h-5 w-5 text-green-500" />
                      Menubar 菜单栏
                    </CardTitle>
                    <CardDescription>应用程序菜单栏</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Menubar>
                      <MenubarMenu>
                        <MenubarTrigger>文件</MenubarTrigger>
                        <MenubarContent>
                          <MenubarItem>新建文件</MenubarItem>
                          <MenubarItem>打开文件</MenubarItem>
                          <MenubarSeparator />
                          <MenubarItem>保存</MenubarItem>
                        </MenubarContent>
                      </MenubarMenu>
                      <MenubarMenu>
                        <MenubarTrigger>编辑</MenubarTrigger>
                        <MenubarContent>
                          <MenubarItem>撤销</MenubarItem>
                          <MenubarItem>重做</MenubarItem>
                        </MenubarContent>
                      </MenubarMenu>
                    </Menubar>
                  </CardContent>
                </Card>

                <!-- 下拉菜单 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ChevronDown class="h-5 w-5 text-purple-500" />
                      DropdownMenu 下拉菜单
                    </CardTitle>
                    <CardDescription>可定制的下拉菜单</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <DropdownMenu>
                      <DropdownMenuTrigger as-child>
                        <Button variant="outline">
                          打开菜单
                          <ChevronDown class="ml-2 h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent class="w-56">
                        <DropdownMenuItem>
                          <User class="mr-2 h-4 w-4" />
                          个人资料
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Settings class="mr-2 h-4 w-4" />
                          设置
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>
                          退出登录
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </CardContent>
                </Card>

                <!-- 上下文菜单 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <MousePointer class="h-5 w-5 text-orange-500" />
                      ContextMenu 上下文菜单
                    </CardTitle>
                    <CardDescription>右键上下文菜单</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ContextMenu>
                      <ContextMenuTrigger class="flex h-20 w-full items-center justify-center rounded-md border border-dashed text-sm">
                        右键点击这里
                      </ContextMenuTrigger>
                      <ContextMenuContent class="w-64">
                        <ContextMenuItem>复制</ContextMenuItem>
                        <ContextMenuItem>粘贴</ContextMenuItem>
                        <ContextMenuSeparator />
                        <ContextMenuItem>删除</ContextMenuItem>
                      </ContextMenuContent>
                    </ContextMenu>
                  </CardContent>
                </Card>

                <!-- 分页 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ChevronDown class="h-5 w-5 text-teal-500" />
                      Pagination 分页
                    </CardTitle>
                    <CardDescription>数据分页导航</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Pagination :total="100" :page="currentPage" :items-per-page="10" @update:page="handlePageChange">
                      <PaginationContent>
                        <PaginationItem :value="1">
                          <PaginationPrevious href="#" />
                        </PaginationItem>
                        <PaginationItem :value="1">
                          <span class="px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md">1</span>
                        </PaginationItem>
                        <PaginationItem :value="2">
                          <span class="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 rounded-md cursor-pointer">2</span>
                        </PaginationItem>
                        <PaginationItem :value="3">
                          <PaginationEllipsis />
                        </PaginationItem>
                        <PaginationItem :value="10">
                          <PaginationNext href="#" />
                        </PaginationItem>
                      </PaginationContent>
                    </Pagination>
                  </CardContent>
                </Card>

                <!-- 指令组件 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Settings class="h-5 w-5 text-pink-500" />
                      Command 指令
                    </CardTitle>
                    <CardDescription>快速搜索指令面板</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Command class="rounded-lg border shadow-md">
                      <CommandInput placeholder="输入搜索..." />
                      <CommandList>
                        <CommandEmpty>没有找到结果。</CommandEmpty>
                        <CommandGroup heading="建议">
                          <CommandItem value="calendar">
                            <Calendar class="mr-2 h-4 w-4" />
                            <span>日历</span>
                          </CommandItem>
                          <CommandItem value="user">
                            <User class="mr-2 h-4 w-4" />
                            <span>用户设置</span>
                          </CommandItem>
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <!-- 高级组件 -->
            <TabsContent value="advanced" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- 表格 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Square class="h-5 w-5 text-blue-500" />
                      Table 表格
                    </CardTitle>
                    <CardDescription>数据表格展示</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableCaption>用户列表</TableCaption>
                      <TableHeader>
                        <TableRow>
                          <TableHead>姓名</TableHead>
                          <TableHead>状态</TableHead>
                          <TableHead>操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow>
                          <TableCell class="font-medium">张三</TableCell>
                          <TableCell>
                            <Badge variant="default">在线</Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">编辑</Button>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell class="font-medium">李四</TableCell>
                          <TableCell>
                            <Badge variant="secondary">离线</Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">编辑</Button>
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>

                <!-- 日历 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Calendar class="h-5 w-5 text-green-500" />
                      Calendar 日历
                    </CardTitle>
                    <CardDescription>日期选择组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <CalendarComponent v-model="selectedDate" mode="single" />
                  </CardContent>
                </Card>

                <!-- 轮播图 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <MousePointer class="h-5 w-5 text-purple-500" />
                      Carousel 轮播图
                    </CardTitle>
                    <CardDescription>图片轮播组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Carousel class="w-full max-w-xs">
                      <CarouselContent>
                        <CarouselItem v-for="i in 5" :key="i">
                          <Card>
                            <CardContent class="flex aspect-square items-center justify-center p-6">
                              <span class="text-4xl font-semibold">{{ i }}</span>
                            </CardContent>
                          </Card>
                        </CarouselItem>
                      </CarouselContent>
                      <CarouselPrevious />
                      <CarouselNext />
                    </Carousel>
                  </CardContent>
                </Card>

                <!-- 折叠面板 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ChevronDown class="h-5 w-5 text-orange-500" />
                      Collapsible 折叠面板
                    </CardTitle>
                    <CardDescription>可折叠内容区域</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Collapsible v-model:open="isCollapsibleOpen">
                      <div class="flex items-center justify-between space-x-4 px-4">
                        <h4 class="text-sm font-semibold">
                          设置选项
                        </h4>
                        <CollapsibleTrigger as-child>
                          <Button variant="ghost" size="sm">
                            <ChevronDown class="h-4 w-4" />
                          </Button>
                        </CollapsibleTrigger>
                      </div>
                      <CollapsibleContent class="space-y-2">
                        <div class="rounded-md border px-4 py-2 text-sm">
                          选项 1
                        </div>
                        <div class="rounded-md border px-4 py-2 text-sm">
                          选项 2
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </CardContent>
                </Card>

                <!-- 组合框 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <ChevronDown class="h-5 w-5 text-teal-500" />
                      Combobox 组合框
                    </CardTitle>
                    <CardDescription>搜索选择组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Combobox v-model="comboboxValue">
                      <ComboboxInput placeholder="搜索选项..." />
                      <ComboboxList>
                        <ComboboxItem v-for="option in comboboxOptions" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </ComboboxItem>
                      </ComboboxList>
                    </Combobox>
                  </CardContent>
                </Card>

                <!-- 侧边栏 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Layers class="h-5 w-5 text-pink-500" />
                      Sheet 侧边栏
                    </CardTitle>
                    <CardDescription>抽屉式侧边栏</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Sheet v-model:open="sheetOpen">
                      <SheetTrigger as-child>
                        <Button variant="outline">打开侧边栏</Button>
                      </SheetTrigger>
                      <SheetContent>
                        <SheetHeader>
                          <SheetTitle>侧边栏标题</SheetTitle>
                          <SheetDescription>
                            这里是侧边栏的内容描述。
                          </SheetDescription>
                        </SheetHeader>
                        <div class="grid gap-4 py-4">
                          <div class="space-y-2">
                            <Label for="name">姓名</Label>
                            <Input id="name" value="张三" />
                          </div>
                          <div class="space-y-2">
                            <Label for="email">邮箱</Label>
                            <Input id="email" value="zhang@example.com" />
                          </div>
                        </div>
                        <SheetFooter>
                          <SheetClose as-child>
                            <Button type="submit">保存更改</Button>
                          </SheetClose>
                        </SheetFooter>
                      </SheetContent>
                    </Sheet>
                  </CardContent>
                </Card>

                <!-- 抽屉 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Square class="h-5 w-5 text-indigo-500" />
                      Drawer 抽屉
                    </CardTitle>
                    <CardDescription>底部弹出抽屉</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Drawer v-model:open="drawerOpen">
                      <DrawerTrigger as-child>
                        <Button variant="outline">打开抽屉</Button>
                      </DrawerTrigger>
                      <DrawerContent>
                        <div class="mx-auto w-full max-w-sm">
                          <DrawerHeader>
                            <DrawerTitle>抽屉标题</DrawerTitle>
                            <DrawerDescription>这里是抽屉的内容。</DrawerDescription>
                          </DrawerHeader>
                          <div class="p-4 pb-0">
                            <div class="flex items-center justify-center space-x-2">
                              <Button variant="outline" size="icon" @click="count > 0 && count--">
                                <Minus class="h-4 w-4" />
                              </Button>
                              <div class="flex-1 text-center">
                                <div class="text-7xl font-bold tracking-tighter">
                                  {{ count }}
                                </div>
                                <div class="text-[0.70rem] uppercase text-muted-foreground">
                                  计数器
                                </div>
                              </div>
                              <Button variant="outline" size="icon" @click="count++">
                                <Plus class="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                          <DrawerFooter>
                            <Button>确认</Button>
                            <DrawerClose as-child>
                              <Button variant="outline">取消</Button>
                            </DrawerClose>
                          </DrawerFooter>
                        </div>
                      </DrawerContent>
                    </Drawer>
                  </CardContent>
                </Card>

                <!-- 可调整大小 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <SlidersHorizontal class="h-5 w-5 text-green-500" />
                      Resizable 可调整大小
                    </CardTitle>
                    <CardDescription>可调整大小的面板</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResizablePanelGroup direction="horizontal" class="max-w-md rounded-lg border">
                      <ResizablePanel :default-size="50">
                        <div class="flex h-[200px] items-center justify-center p-6">
                          <span class="font-semibold">面板 1</span>
                        </div>
                      </ResizablePanel>
                      <ResizableHandle />
                      <ResizablePanel :default-size="50">
                        <div class="flex h-[200px] items-center justify-center p-6">
                          <span class="font-semibold">面板 2</span>
                        </div>
                      </ResizablePanel>
                    </ResizablePanelGroup>
                  </CardContent>
                </Card>

                <!-- 步骤器 -->
                <Card class="shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle class="flex items-center gap-2">
                      <Circle class="h-5 w-5 text-purple-500" />
                      Stepper 步骤器
                    </CardTitle>
                    <CardDescription>引导步骤组件</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Stepper v-model="currentStep" class="w-full">
                      <StepperItem :step="1">
                        <StepperTrigger>
                          <StepperIndicator />
                          步骤 1
                        </StepperTrigger>
                        <div class="mt-2">
                          <StepperTitle>基本信息</StepperTitle>
                          <StepperDescription>填写您的基本信息</StepperDescription>
                        </div>
                      </StepperItem>
                      <StepperItem :step="2">
                        <StepperTrigger>
                          <StepperIndicator />
                          步骤 2
                        </StepperTrigger>
                        <div class="mt-2">
                          <StepperTitle>详细设置</StepperTitle>
                          <StepperDescription>配置详细设置</StepperDescription>
                        </div>
                      </StepperItem>
                      <StepperItem :step="3">
                        <StepperTrigger>
                          <StepperIndicator />
                          步骤 3
                        </StepperTrigger>
                        <div class="mt-2">
                          <StepperTitle>完成</StepperTitle>
                          <StepperDescription>确认并完成设置</StepperDescription>
                        </div>
                      </StepperItem>
                    </Stepper>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        <!-- 底部信息 -->
        <div class="text-center text-gray-500 dark:text-gray-400">
          <p class="text-sm">
            基于 <a href="https://www.shadcn-vue.com/" class="text-blue-500 hover:underline" target="_blank">shadcn-vue</a> 
            构建的现代化 Vue 3 组件库
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Icons
import {
  User, Bot, MousePointer, Tag, BarChart3, 
  AlertTriangle, Info, Loader2, Star, ToggleLeft, ToggleRight,
  Bold, Italic, Underline, SlidersHorizontal, Type, AlignLeft,
  ChevronDown, CheckSquare, Circle, Calendar, Square, Minus,
  ScrollText, Navigation, MessageSquare, Copy, HelpCircle,
  Plus, Settings, MessageCircle, Layers
} from 'lucide-vue-next'

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Toggle } from '@/components/ui/toggle'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Slider } from '@/components/ui/slider'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from '@/components/ui/dialog'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import Progress from '@/components/ui/Progress.vue'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import Skeleton from '@/components/ui/Skeleton.vue'

// Navigation Components
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger } from '@/components/ui/navigation-menu'
import { Menubar, MenubarContent, MenubarItem, MenubarMenu, MenubarSeparator, MenubarTrigger } from '@/components/ui/menubar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { ContextMenu, ContextMenuContent, ContextMenuItem, ContextMenuSeparator, ContextMenuTrigger } from '@/components/ui/context-menu'
import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationNext, PaginationPrevious } from '@/components/ui/pagination'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'

// Advanced Components
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Calendar as CalendarComponent } from '@/components/ui/calendar'
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Combobox, ComboboxInput, ComboboxItem, ComboboxList } from '@/components/ui/combobox'
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from '@/components/ui/drawer'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import { Stepper, StepperIndicator, StepperItem, StepperTrigger, StepperTitle, StepperDescription } from '@/components/ui/stepper'

// State
const activeTab = ref('basic')
const demoTabValue = ref('tab1')

// Form states
const switch1 = ref(false)
const switch2 = ref(true)
const switch3 = ref(false)
const toggle1 = ref(false)
const toggle2 = ref(false)
const toggle3 = ref(false)
const toggleGroup = ref(['bold'])
const sliderValue1 = ref([50])
const sliderValue2 = ref([20, 80])
const inputValue1 = ref('')
const inputValue2 = ref('')
const inputValue3 = ref('')
const textareaValue = ref('')
const selectValue = ref('')
const checkbox1 = ref(false)
const checkbox2 = ref(true)
const checkbox3 = ref(false)
const radioValue = ref('option1')

// Dialog and modal states
const dialogOpen = ref(false)
const sheetOpen = ref(false)
const drawerOpen = ref(false)

// Progress state
const progressValue = ref(33)

// Navigation states
const currentPage = ref(1)

// Advanced component states
const selectedDate = ref()
const isCollapsibleOpen = ref(false)
const comboboxValue = ref('')
const comboboxOptions = [
  { value: 'react', label: 'React' },
  { value: 'vue', label: 'Vue' },
  { value: 'angular', label: 'Angular' },
  { value: 'svelte', label: 'Svelte' }
]
const currentStep = ref(1)
const count = ref(0)

// Functions
const simulateProgress = () => {
  progressValue.value = 0
  const interval = setInterval(() => {
    if (progressValue.value < 100) {
      progressValue.value += 10
    } else {
      clearInterval(interval)
    }
  }, 200)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}
</script>