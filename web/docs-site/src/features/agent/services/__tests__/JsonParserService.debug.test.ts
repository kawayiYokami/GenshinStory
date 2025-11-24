import { describe, it, expect, beforeEach } from 'vitest';
import { JsonParserService } from '../JsonParserService';

describe('调试 JsonParserService', () => {
  let parser: JsonParserService;

  beforeEach(() => {
    parser = new JsonParserService();
  });

  it('应该提取多行JSON', () => {
    const testContent = `文本开始
{
  "tool_call": {
    "name": "search",
    "arguments": {
      "query": "测试搜索"
    }
  }
}
文本结束`;

    const result = parser.extractJson(testContent);

    console.log('提取结果:', result ? '成功' : '失败');
    if (result) {
      console.log('JSON内容:', JSON.stringify(result.json, null, 2));
      console.log('位置信息:', {
        startIndex: result.startIndex,
        endIndex: result.endIndex,
        original: result.original
      });
    }

    expect(result).toBeTruthy();
    if (result) {
      expect(result.json.tool_call).toBeDefined();
      expect(result.json.tool_call.name).toBe('search');
    }
  });

  it('应该提取简单JSON', () => {
    const testContent = '前面文本{"tool_call":{"name":"ask","arguments":{"question":"测试问题"}}}后面文本';

    const result = parser.extractJson(testContent);

    console.log('简单JSON提取结果:', result ? '成功' : '失败');
    if (result) {
      console.log('JSON内容:', JSON.stringify(result.json, null, 2));
      console.log('位置信息:', {
        startIndex: result.startIndex,
        endIndex: result.endIndex,
        original: result.original
      });
    }

    expect(result).toBeTruthy();
    if (result) {
      expect(result.json.tool_call).toBeDefined();
      expect(result.json.tool_call.name).toBe('ask');
    }
  });
});