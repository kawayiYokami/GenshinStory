import { describe, it, expect } from 'vitest';
import parserAdapter, { parseJsonToolCallFormat } from '../parserAdapter';

describe('调试 parserAdapter', () => {
  it('应该解析工具调用JSON', () => {
    const jsonString = '{"tool_call":{"name":"search","arguments":{"query":"测试搜索"}}}';

    console.log('输入的JSON字符串:', jsonString);

    // 直接使用函数
    try {
      const result = parseJsonToolCallFormat(jsonString);
      console.log('parseJsonToolCallFormat结果:', result);

      if (result) {
        console.log('工具名称:', result.name);
        console.log('工具参数:', result.params);
      } else {
        console.log('parseJsonToolCallFormat返回null，检查是否是name问题');
        const parsed = JSON.parse(jsonString);
        console.log('tool_call字段存在:', 'tool_call' in parsed);
        console.log('tool_call值:', parsed.tool_call);
        console.log('tool_call类型:', typeof parsed.tool_call);

        if (parsed.tool_call && typeof parsed.tool_call === 'object') {
          const name = parsed.tool_call.name;
          console.log('提取的name:', name);
          console.log('VALID_TOOLS包含search:', ['search_docs', 'read_doc', 'list_docs', 'ask'].includes(name));
        }
      }
    } catch (error) {
      console.log('parseJsonToolCallFormat失败:', error);
    }

    // 使用默认导出
    try {
      const adapterResult = parserAdapter.parseSingleToolCall(jsonString);
      console.log('parserAdapter结果:', adapterResult);
    } catch (error) {
      console.log('parserAdapter失败:', error);
    }

    expect(true).toBe(true); // 这个测试只是为了调试
  });
});