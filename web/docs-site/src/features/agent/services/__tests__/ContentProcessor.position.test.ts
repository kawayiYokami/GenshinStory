import { describe, it, expect } from 'vitest';
import { ContentProcessor } from '../ContentProcessor';

describe('ContentProcessor 位置信息实现测试（修正）', () => {
  describe('精确删除功能', () => {
    it('应该精确删除简单的工具调用JSON', () => {
      const testContent = '前面文本{"tool_call":{"name":"ask","arguments":{"question":"测试问题"}}}后面文本';
      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('ask');
      expect(result.toolCalls[0].params.question).toBe('测试问题');
      expect(result.cleanedContent).toBe('前面文本后面文本');
    });

    it('应该处理多行格式的JSON工具调用', () => {
      const testContent = `文本开始
{
  "tool_call": {
    "name": "search_docs",
    "arguments": {
      "query": "测试搜索"
    }
  }
}
文本结束`;

      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('search_docs');
      expect(result.toolCalls[0].params.query).toBe('测试搜索');
      expect(result.cleanedContent.trim()).toBe('文本开始\n\n文本结束');
    });

    it('应该从多个JSON中正确识别并删除工具调用', () => {
      const testContent = '前面的{"data":"这不是工具调用"}然后{"tool_call":{"name":"ask","arguments":{"question":"真正的工具调用"}}}最后的{"other":"另一个JSON"}';

      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('ask');
      expect(result.toolCalls[0].params.question).toBe('真正的工具调用');
      expect(result.cleanedContent).toContain('前面的{"data":"这不是工具调用"}然后');
      expect(result.cleanedContent).toContain('最后的{"other":"另一个JSON"}');
      expect(result.cleanedContent).not.toContain('{"tool_call":');
    });

    it('应该正确处理嵌套字符串中的花括号', () => {
      const testContent = '文本{"tool_call":{"name":"ask","arguments":{"question":"这里有大括号{test}不会被误判"}}}更多文本';

      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('ask');
      expect(result.toolCalls[0].params.question).toBe('这里有大括号{test}不会被误判');
      expect(result.cleanedContent).toBe('文本更多文本');
    });

    it('应该对没有工具调用的内容保持原样', () => {
      const testContent = '这只是普通文本{"data":"普通JSON"}没有工具调用';

      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(0);
      expect(result.cleanedContent).toBe(testContent.replace(/\n\s*\n\s*\n/g, '\n\n').trim());
    });

    it('应该处理工具调用中有转义字符的情况', () => {
      const testContent = '开始{"tool_call":{"name":"ask","arguments":{"question":"包含\\"引号\\"的问题"}}}结束';

      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('ask');
      expect(result.toolCalls[0].params.question).toBe('包含"引号"的问题');
      expect(result.cleanedContent).toBe('开始结束');
    });
  });

  describe('边界情况', () => {
    it('应该处理空字符串', () => {
      const result = ContentProcessor.extract('');

      expect(result.toolCalls).toHaveLength(0);
      expect(result.cleanedContent).toBe('');
    });

    it('应该处理只有JSON的情况', () => {
      const testContent = '{"tool_call":{"name":"ask","arguments":{"question":"测试问题"}}}';

      const result = ContentProcessor.extract(testContent);

      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('ask');
      expect(result.toolCalls[0].params.question).toBe('测试问题');
      expect(result.cleanedContent).toBe('');
    });

    it('应该处理连续的工具调用', () => {
      const testContent = '第一个{"tool_call":{"name":"ask","arguments":{"question":"问题1"}}}第二个{"tool_call":{"name":"ask","arguments":{"question":"问题2"}}}第三个';

      const result = ContentProcessor.extract(testContent);

      // AI不会连续发送多个工具调用，只处理第一个
      expect(result.toolCalls).toHaveLength(1);
      expect(result.toolCalls[0].name).toBe('ask');
      expect(result.toolCalls[0].params.question).toBe('问题1');

      // 第一个工具调用应该被删除，其他保留
      expect(result.cleanedContent).toContain('第一个');
      expect(result.cleanedContent).toContain('第二个');
      expect(result.cleanedContent).toContain('第三个');
      // 但第一个工具调用的JSON部分应该被删除
      expect(result.cleanedContent).not.toContain('问题1');
      // 第二个工具调用应该保留（因为只处理第一个）
      expect(result.cleanedContent).toContain('问题2');
    });
  });

  describe('一致性验证', () => {
    it('extract和reconstruct应该保持一致性', () => {
      const testContent = '前面{"tool_call":{"name":"ask","arguments":{"question":"测试问题"}}}后面';

      const extracted = ContentProcessor.extract(testContent);
      const reconstructed = ContentProcessor.reconstruct(extracted, {
        includeToolCalls: true,
        toolCallFormat: 'original'
      });

      // 重建后的内容应该包含原始的工具调用JSON
      expect(reconstructed).toContain('{"tool_call":');
      expect(reconstructed).toContain('前面');
      expect(reconstructed).toContain('后面');
    });
  });
});