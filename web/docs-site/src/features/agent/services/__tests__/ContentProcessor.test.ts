import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ContentProcessor } from '../ContentProcessor';
import type { ParsedToolCall } from '../toolParserService';

// Mock dependencies
vi.mock('@/features/app/services/loggerService', () => ({
  default: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn()
  }
}));

vi.mock('../jsonParserService', () => ({
  jsonParserService: {
    extractJson: vi.fn((content: string) => {
      // 直接返回预定义的结果以避免JSON解析错误
      const jsonString1 = '{"name": "test_tool", "arguments": {"param": "value"}}';
      const jsonString2 = '{"name": "tool1", "arguments": {}}';
      const jsonString3 = '{"name": "tool2", "arguments": {}}';
      const jsonString4 = '{"name": "test", "arguments": {"nested": {"value": 1}}}';
      const jsonString5 = '{"name": "test", "arguments": {}}';

      if (content.includes(jsonString1)) {
        return [{
          original: jsonString1,
          parsed: { name: "test_tool", arguments: { param: "value" } }
        }];
      } else if (content.includes(jsonString2) && content.includes(jsonString3)) {
        return [
          { original: jsonString2, parsed: { name: "tool1", arguments: {} } },
          { original: jsonString3, parsed: { name: "tool2", arguments: {} } }
        ];
      } else if (content.includes(jsonString4)) {
        return [{
          original: jsonString4,
          parsed: { name: "test", arguments: { nested: { value: 1 } } }
        }];
      } else if (content.includes(jsonString5)) {
        return [{
          original: jsonString5,
          parsed: { name: "test", arguments: {} }
        }];
      }

      return [];
    })
  }
}));

vi.mock('../toolParserService', () => ({
  toolParserService: {
    parseToolCall: vi.fn((jsonString: string) => {
      try {
        const parsed = JSON.parse(jsonString);
        if (parsed.name) {
          return {
            name: parsed.name,
            args: parsed.arguments || parsed.params || {},
            original: jsonString
          };
        }
        return null;
      } catch {
        return null;
      }
    })
  }
}));

describe('ContentProcessor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('extract', () => {
    it('should extract tool calls and clean content', () => {
      const content = '这是一些文本内容\n\n{"name": "test_tool", "arguments": {"param": "value"}}\n\n更多文本内容';

      const result = ContentProcessor.extract(content);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('test_tool');
      expect(result.cleanedContent).toContain('这是一些文本内容');
      expect(result.cleanedContent).toContain('更多文本内容');
      expect(result.cleanedContent).not.toContain('{"name": "test_tool"');
    });

    it('should handle multiple tool calls', () => {
      const content = '开始文本\n\n{"name": "tool1", "arguments": {}}\n\n中间文本\n\n{"name": "tool2", "arguments": {}}\n\n结束文本';

      const result = ContentProcessor.extract(content);

      expect(result.toolCalls).toHaveLength(2);
      expect(result.toolCalls[0].name).toBe('tool1');
      expect(result.toolCalls[1].name).toBe('tool2');
      expect(result.cleanedContent).toContain('开始文本');
      expect(result.cleanedContent).toContain('中间文本');
      expect(result.cleanedContent).toContain('结束文本');
    });

    it('should handle content without tool calls', () => {
      const content = '这是普通的文本内容\n\n没有工具调用';

      const result = ContentProcessor.extract(content);

      expect(result.toolCalls).toHaveLength(0);
      expect(result.cleanedContent).toBe(content);
    });

    it('should preserve original content in the result', () => {
      const content = '测试内容\n\n{"name": "test", "arguments": {}}';

      const result = ContentProcessor.extract(content);

      expect(result.originalContent).toBe(content);
    });
  });

  describe('reconstruct', () => {
    it('should reconstruct original content with tool calls', () => {
      const originalContent = '开始文本\n\n{"name": "test", "arguments": {"param": "value"}}\n\n结束文本';
      const extracted = ContentProcessor.extract(originalContent);

      const reconstructed = ContentProcessor.reconstruct(extracted);

      expect(reconstructed).toBe(originalContent);
    });

    it('should return only cleaned content when tool calls are excluded', () => {
      const originalContent = '开始文本\n\n{"name": "test", "arguments": {}}\n\n结束文本';
      const extracted = ContentProcessor.extract(originalContent);

      expect(extracted.toolCalls).toHaveLength(1);
      expect(extracted.cleanedContent).toContain('开始文本');
      expect(extracted.cleanedContent).toContain('结束文本');
      expect(extracted.cleanedContent).not.toContain('{"name": "test"');

      const reconstructed = ContentProcessor.reconstruct(extracted, { includeToolCalls: false });

      expect(reconstructed).toBe(extracted.cleanedContent);
      expect(reconstructed).not.toContain('{"name": "test"');
    });

    it('should format tool calls when formatted option is used', () => {
      const originalContent = '文本\n\n{"name": "test", "arguments": {"nested": {"value": 1}}}\n\n更多文本';
      const extracted = ContentProcessor.extract(originalContent);

      const reconstructed = ContentProcessor.reconstruct(extracted, { toolCallFormat: 'formatted' });

      expect(reconstructed).toContain('"nested": {\n    "value": 1\n  }');
    });
  });

  describe('hasToolCalls', () => {
    it('should return true when content contains tool calls', () => {
      const content = '文本\n\n{"name": "test", "arguments": {"param": "value"}}\n\n更多文本';

      const result = ContentProcessor.extract(content);
      console.log('Test result toolCalls:', result.toolCalls);
      expect(result.toolCalls.length).toBeGreaterThan(0);
      expect(ContentProcessor.hasToolCalls(content)).toBe(true);
    });

    it('should return false when content does not contain tool calls', () => {
      const content = '普通文本内容\n\n没有工具调用';

      expect(ContentProcessor.hasToolCalls(content)).toBe(false);
    });
  });

  describe('getToolCallCount', () => {
    it('should return correct count of tool calls', () => {
      const content = '开始\n\n{"name": "tool1", "arguments": {}}\n\n中间\n\n{"name": "tool2", "arguments": {}}\n\n结束';

      expect(ContentProcessor.getToolCallCount(content)).toBe(2);
    });

    it('should return zero when no tool calls exist', () => {
      const content = '普通文本内容';

      expect(ContentProcessor.getToolCallCount(content)).toBe(0);
    });
  });

  describe('validateConsistency', () => {
    it('should validate consistent extract and reconstruct cycle', () => {
      const content = '测试内容\n\n{"name": "test", "arguments": {"param": "value"}}\n\n更多内容';

      expect(ContentProcessor.validateConsistency(content)).toBe(true);
    });

    it('should return false for inconsistent processing', () => {
      // 模拟不一致的情况
      const mockProcessed = {
        cleanedContent: '部分内容',
        toolCalls: [
          { name: 'test', params: { param: 'value' }, original: '{"modified": "content"}' } as ParsedToolCall
        ],
        originalContent: '原始内容'
      };

      const reconstructed = ContentProcessor.reconstruct(mockProcessed);
      expect(reconstructed).not.toBe(mockProcessed.originalContent);
    });
  });
});