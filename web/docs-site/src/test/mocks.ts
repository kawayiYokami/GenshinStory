import { vi } from 'vitest'
import type { Tool } from '@/features/agent/tools/tool'
import type { Session, Message } from '@/features/agent/types'
import type { MessageManager } from '@/features/agent/stores/messageManager'

// 创建 Mock Tool
export function createMockTool<T = any>(overrides: Partial<Tool<T>> = {}): Tool<T> {
  return {
    name: 'mock_tool',
    type: 'execution',
    description: 'Mock tool for testing',
    usage: '<mock_tool><param>value</param></mock_tool>',
    examples: ['<mock_tool><param>test</param></mock_tool>'],
    error_guidance: 'This is a mock tool',
    execute: vi.fn().mockResolvedValue({ result: 'Mock result' }),
    ...overrides
  }
}

// 创建 Mock Session
export function createMockSession(overrides: Partial<Session> = {}): Session {
  const now = new Date().toISOString()
  return {
    id: 'test-session-id',
    domain: 'test-domain',
    roleId: 'test-role-id',
    name: 'Test Session',
    createdAt: now,
    messageIds: [],
    messagesById: {},
    ...overrides
  }
}

// 创建 Mock Message
export function createMockMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: 'test-message-id',
    role: 'user',
    content: 'Test message',
    type: 'text',
    createdAt: new Date().toISOString(),
    ...overrides
  }
}

// 创建 Mock MessageManager
export function createMockMessageManager(): MessageManager {
  return {
    addMessage: vi.fn(),
    updateMessage: vi.fn(),
    replaceMessage: vi.fn(),
    deleteMessage: vi.fn(),
    getMessage: vi.fn(),
    getMessages: vi.fn(),
    clearMessages: vi.fn()
  } as any
}

// 创建带消息的 Mock Session
export function createMockSessionWithMessages(messages: Message[]): Session {
  const session = createMockSession()
  messages.forEach(msg => {
    session.messageIds.push(msg.id)
    session.messagesById[msg.id] = msg
  })
  return session
}

// 模拟 AI 响应的工具调用
export const mockToolCalls = [
  {
    id: 'call_1',
    type: 'function' as const,
    function: {
      name: 'search_docs',
      arguments: JSON.stringify({ query: 'Vue 3 composition API' })
    }
  },
  {
    id: 'call_2',
    type: 'function' as const,
    function: {
      name: 'read_doc',
      arguments: JSON.stringify({
        args: '<doc><path>/src/components/Test.vue</path></doc>'
      })
    }
  }
]

// 模拟 XML 格式的工具调用
export const mockXmlToolCalls = [
  `<search_docs>
  <query>Vue 3 composition API</query>
</search_docs>`,
  `<read_doc>
  <doc>
    <path>/src/components/Test.vue</path>
    <line_range>1-20</line_range>
  </doc>
</read_doc>`,
  `<list_docs>
  <path>/src/components</path>
</list_docs>`
]

// 模拟复杂的嵌套 XML
export const complexXmlExample = `<read_doc>
  <doc>
    <path>/src/features/agent/services/toolParserService.ts</path>
    <line_range>77-120</line_range>
    <metadata>
      <type>typescript</type>
      <size>2.5KB</size>
    </metadata>
  </doc>
  <doc>
    <path>/src/features/agent/tools/read_doc.ts</path>
  </doc>
</read_doc>`

// 模拟带有换行和格式的 XML
export const formattedXmlExample = `<search_docs>
  <query>
    Vue 3 composition API tutorial
    for beginners 2024
  </query>
  <filter>
    <type>documentation</type>
    <language>english</language>
  </filter>
</search_docs>`

// 模拟无效的 XML
export const invalidXmlExamples = [
  '<unclosed>',
  '<search_docs><query>',
  'not xml at all',
  '<search_docs></invalid_tool>',
  '{"not": "xml"}'
]

// 工具执行结果模拟
export const mockToolResults = {
  search_docs: {
    result: `# 搜索结果

找到 5 个相关文档：

1. **Vue 3 Composition API Guide**
   - 路径: /docs/vue3/composition-api.md
   - 大小: 15KB
   - 最后修改: 2024-01-15

2. **Reactivity in Vue 3**
   - 路径: /docs/vue3/reactivity.md
   - 大小: 8KB
   - 最后修改: 2024-01-10

建议使用 read_doc 工具查看具体内容。`
  },
  read_doc: {
    result: `# /src/components/Test.vue

\`\`\`vue
<template>
  <div class="test-component">
    <h1>{{ title }}</h1>
    <button @click="increment">Count: {{ count }}</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const title = ref('Test Component')
const count = ref(0)

const increment = () => {
  count.value++
}
</script>
\`\`\`

这是一个简单的 Vue 3 组件示例。`
  },
  list_docs: {
    result: `# /src/components 目录

📁 components/
├── Test.vue
├── UserProfile.vue
├── Navigation.vue
└── Layout/

共 4 个文件，1 个目录`
  }
}

// 模拟错误情况
export const mockErrors = {
  toolNotFound: {
    result: '错误：未知的工具 \'invalid_tool\''
  },
  parseError: {
    result: '错误：解析工具参数时发生异常'
  },
  executionError: {
    result: '错误：执行工具 \'search_docs\' 时发生异常: Network error'
  }
}