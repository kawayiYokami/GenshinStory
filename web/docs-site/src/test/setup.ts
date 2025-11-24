import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// 全局 mock
vi.mock('@/features/app/services/loggerService', () => ({
  default: {
    log: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn(),
    info: vi.fn()
  }
}))

vi.mock('@/features/agent/services/toolPromptService', () => ({
  toolPromptService: {
    getPrompt: vi.fn()
  }
}))

vi.mock('@/features/agent/tools/toolRegistryService', () => ({
  toolRegistryService: {
    getTool: vi.fn(),
    getFollowUpTools: vi.fn()
  }
}))

vi.mock('@/features/agent/tools/toolStateService', () => ({
  toolStateService: {
    hasPromptBeenSent: vi.fn(),
    markPromptAsSent: vi.fn()
  }
}))

vi.mock('@/lib/tokenizer/tokenizerService', () => ({
  default: {
    countTokens: vi.fn()
  }
}))

vi.mock('@/features/agent/services/contextOptimizerService', () => ({
  default: {
    calculateHistoryTokens: vi.fn()
  }
}))

// 全局测试配置
config.global.stubs = {
  'transition': true,
  'transition-group': true
}