<template>
  <div class="min-h-screen bg-base-100 overflow-y-auto">
    <div class="container mx-auto p-8 max-w-4xl">
      <h1 class="text-3xl font-bold mb-8">列表容器下拉框解决方案</h1>

      <!-- 技术说明 -->
      <div class="mb-8 p-6 bg-info/10 rounded-lg border border-info/20">
        <h2 class="text-xl font-semibold mb-4 text-info">技术说明</h2>
        <div class="space-y-2 text-base-content/80">
          <p><strong>问题背景：</strong> DaisyUI v5的menu组件在使用overflow-y-auto时存在无法修复的框架级问题</p>
          <p><strong>解决方案：</strong> 使用div+ul+li结构替代DaisyUI menu组件，自定义滚动区域</p>
          <p><strong>技术优势：</strong> 完全可控的滚动行为、语义化的HTML结构、灵活的内容展示</p>
        </div>
      </div>

      <!-- 基础列表容器下拉框 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">基础列表容器下拉框</h2>
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn m-1">基础列表容器</div>
          <div tabindex="0" class="dropdown-content bg-base-100 rounded-box w-64 shadow-md border">
            <ul class="p-2 space-y-1">
              <li>
                <a class="block px-3 py-2 hover:bg-base-200 rounded-lg transition-colors">
                  选项 1
                </a>
              </li>
              <li>
                <a class="block px-3 py-2 hover:bg-base-200 rounded-lg transition-colors">
                  选项 2
                </a>
              </li>
              <li>
                <a class="block px-3 py-2 hover:bg-base-200 rounded-lg transition-colors">
                  选项 3
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 带滚动的列表容器 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">带滚动的列表容器</h2>
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn m-1">滚动列表容器</div>
          <div tabindex="0" class="dropdown-content bg-base-100 rounded-box w-64 shadow-md border">
            <div class="max-h-48 overflow-y-auto">
              <ul class="p-2 space-y-1">
                <li v-for="i in 15" :key="i">
                  <a class="block px-3 py-2 hover:bg-base-200 rounded-lg transition-colors">
                    选项 {{ i }}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 模型选择列表容器 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">模型选择列表容器</h2>
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn m-1">选择AI模型</div>
          <div tabindex="0" class="dropdown-content bg-base-100 rounded-box w-80 shadow-md border">
            <div class="max-h-64 overflow-y-auto">
              <ul class="p-3 space-y-2">
                <li v-for="model in aiModels" :key="model.id">
                  <a class="block p-3 hover:bg-base-200 rounded-lg transition-colors">
                    <div class="font-medium">{{ model.name }}</div>
                    <div class="text-sm text-base-content/60">{{ model.description }}</div>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 带图标的列表容器 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">带图标的列表容器</h2>
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn m-1">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            选择功能
          </div>
          <div tabindex="0" class="dropdown-content bg-base-100 rounded-box w-72 shadow-md border">
            <div class="max-h-56 overflow-y-auto">
              <ul class="p-2 space-y-1">
                <li v-for="feature in features" :key="feature.id">
                  <a class="flex items-center px-3 py-2 hover:bg-base-200 rounded-lg transition-colors">
                    <div class="w-8 h-8 flex items-center justify-center bg-primary/10 text-primary rounded-full mr-3">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="feature.icon"></path>
                      </svg>
                    </div>
                    <div>
                      <div class="font-medium">{{ feature.name }}</div>
                      <div class="text-xs text-base-content/60">{{ feature.description }}</div>
                    </div>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 分组列表容器 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">分组列表容器</h2>
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn m-1">分组选项</div>
          <div tabindex="0" class="dropdown-content bg-base-100 rounded-box w-80 shadow-md border">
            <div class="max-h-72 overflow-y-auto">
              <div class="p-2">
                <div v-for="group in groupedOptions" :key="group.category" class="mb-4 last:mb-0">
                  <div class="px-3 py-2 text-sm font-semibold text-base-content/70 bg-base-200/50 rounded-lg mb-2">
                    {{ group.category }}
                  </div>
                  <ul class="space-y-1">
                    <li v-for="option in group.items" :key="option.id">
                      <a class="block px-3 py-2 ml-2 hover:bg-base-200 rounded-lg transition-colors">
                        {{ option.name }}
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 超大列表容器 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold mb-4">超大列表容器</h2>
        <div class="dropdown">
          <div tabindex="0" role="button" class="btn m-1">超大选择器</div>
          <div tabindex="0" class="dropdown-content bg-base-100 rounded-box w-[600px] shadow-md border">
            <div class="max-h-96 overflow-y-auto">
              <ul class="p-4 space-y-3">
                <li v-for="item in largeList" :key="item.id">
                  <a class="block p-4 hover:bg-base-200 rounded-lg transition-colors">
                    <div class="flex items-start space-x-3">
                      <div class="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white font-bold">
                        {{ item.id }}
                      </div>
                      <div class="flex-1">
                        <div class="font-semibold text-lg">{{ item.name }}</div>
                        <div class="text-base-content/70 mt-1">{{ item.description }}</div>
                        <div class="flex space-x-2 mt-2">
                          <span v-for="tag in item.tags" :key="tag"
                                class="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                            {{ tag }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 实现说明 -->
      <div class="mt-12 p-6 bg-success/10 rounded-lg border border-success/20">
        <h2 class="text-xl font-semibold mb-4 text-success">实现优势</h2>
        <div class="grid md:grid-cols-2 gap-4 text-base-content/80">
          <div>
            <h3 class="font-medium mb-2">✅ 技术优势</h3>
            <ul class="space-y-1 text-sm">
              <li>• 完全可控的滚动行为</li>
              <li>• 语义化的HTML结构</li>
              <li>• 无框架依赖问题</li>
              <li>• 自定义样式灵活</li>
            </ul>
          </div>
          <div>
            <h3 class="font-medium mb-2">🎨 视觉优势</h3>
            <ul class="space-y-1 text-sm">
              <li>• 丰富的内容展示</li>
              <li>• 支持图标和描述</li>
              <li>• 分组和标签支持</li>
              <li>• 一致的交互体验</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// AI模型数据
const aiModels = ref([
  { id: 1, name: 'GPT-4o-mini', description: '快速高效的对话模型' },
  { id: 2, name: 'Claude-3.5-Sonnet-20241022', description: '强大的推理和分析能力' },
  { id: 3, name: 'Gemini-1.5-Pro-002', description: '多模态理解模型' },
  { id: 4, name: 'Qwen2.5-72B-Instruct', description: '中文优化的大型模型' },
  { id: 5, name: 'Llama-3.1-70B-Instruct', description: '开源高性能模型' },
  { id: 6, name: 'Mistral-Large-2407', description: '欧洲顶级AI模型' },
])

// 功能选项数据
const features = ref([
  {
    id: 1,
    name: '文档搜索',
    description: '智能检索文档内容',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'
  },
  {
    id: 2,
    name: '代码生成',
    description: '自动生成代码片段',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4'
  },
  {
    id: 3,
    name: '图像分析',
    description: '智能图像识别分析',
    icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
  },
  {
    id: 4,
    name: '数据分析',
    description: '深度数据洞察',
    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
  },
])

// 分组选项数据
const groupedOptions = ref([
  {
    category: 'AI服务商',
    items: [
      { id: 1, name: 'OpenAI' },
      { id: 2, name: 'Anthropic' },
      { id: 3, name: 'Google' },
    ]
  },
  {
    category: '开源模型',
    items: [
      { id: 4, name: 'Llama' },
      { id: 5, name: 'Mistral' },
      { id: 6, name: 'Qwen' },
    ]
  },
  {
    category: '中文模型',
    items: [
      { id: 7, name: '智谱AI' },
      { id: 8, name: '月之暗面' },
      { id: 9, name: '百川智能' },
    ]
  }
])

// 超大列表数据
const largeList = ref([
  {
    id: 1,
    name: 'GPT-4 Turbo',
    description: '最新版本的GPT-4模型，支持更长的上下文窗口和更准确的响应',
    tags: ['文本生成', '代码助手', '多语言']
  },
  {
    id: 2,
    name: 'Claude-3 Opus',
    description: 'Anthropic的旗舰模型，在复杂推理和创意写作方面表现出色',
    tags: ['推理', '创作', '安全']
  },
  {
    id: 3,
    name: 'Gemini Ultra',
    description: 'Google的多模态AI模型，可以处理文本、图像和音频',
    tags: ['多模态', '图像识别', '音频处理']
  },
  {
    id: 4,
    name: 'PaLM 2',
    description: 'Google的大型语言模型，在数学和科学推理方面表现优异',
    tags: ['数学', '科学', '推理']
  },
  {
    id: 5,
    name: 'LLaMA 2',
    description: 'Meta的开源大型语言模型，可以本地部署和微调',
    tags: ['开源', '本地部署', '微调']
  }
])
</script>