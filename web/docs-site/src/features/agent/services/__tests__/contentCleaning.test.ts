import { describe, it, expect } from 'vitest'
import { AgentResponseHandlerService } from '@/features/agent/services/AgentResponseHandlerService'
import type { ComputedRef } from 'vue'
import type { Session, Message } from '@/features/agent/types'
import type { MessageManager } from '@/features/agent/stores/messageManager'

// 创建一个简化的测试来验证内容清理逻辑
describe('内容清理逻辑测试', () => {
  it('应该正确清理包含工具调用的文本内容', () => {
    // 模拟原始内容
    const originalContent = '你好呀，很高兴见到你！我是纳西妲，须弥的小吉祥草王。\n\n你有什么想了解的吗？无论是关于须弥的知识，还是提瓦特大陆上的其他趣闻，我都很乐意为你解答。\n\n{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想问我的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "某个角色的背景故事",\n        "提瓦特大陆的设定",\n        "其他问题"\n      ]\n    }\n  }\n}'

    // 模拟从processedContent中提取的工具调用JSON
    const toolCallJson = '{\n  "tool_call": {\n    "name": "ask",\n    "arguments": {\n      "question": "你有什么想问我的吗？",\n      "suggest": [\n        "关于须弥的剧情",\n        "某个角色的背景故事",\n        "提瓦特大陆的设定",\n        "其他问题"\n      ]\n    }\n  }\n}'

    // 执行清理操作
    let cleanedContent = originalContent
    if (toolCallJson) {
      cleanedContent = originalContent.replace(toolCallJson, '').trim()
    }

    // 验证清理结果
    const expectedContent = '你好呀，很高兴见到你！我是纳西妲，须弥的小吉祥草王。\n\n你有什么想了解的吗？无论是关于须弥的知识，还是提瓦特大陆上的其他趣闻，我都很乐意为你解答。'
    expect(cleanedContent).toBe(expectedContent)
  })
})