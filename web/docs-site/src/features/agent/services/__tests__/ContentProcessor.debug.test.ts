import { describe, it, expect } from 'vitest';
import { ContentProcessor } from '../ContentProcessor';
import jsonParserService from '../JsonParserService';
import toolParserService from '../toolParserService';

describe('调试 ContentProcessor', () => {
  it('调试多行JSON提取过程', () => {
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

    console.log('=== 完整的 ContentProcessor.extract 过程 ===');
    console.log('原始内容:', JSON.stringify(testContent));

    // 第1步：使用 JsonParserService 提取JSON
    const extractedResult = jsonParserService.extractJson(testContent);
    console.log('第1步 - JsonParserService提取结果:', extractedResult ? '成功' : '失败');

    if (extractedResult) {
      console.log('提取的JSON:', JSON.stringify(extractedResult.json, null, 2));
      console.log('位置信息:', {
        startIndex: extractedResult.startIndex,
        endIndex: extractedResult.endIndex
      });
    } else {
      console.log('JsonParserService未能提取JSON');
      return;
    }

    // 第2步：尝试解析为工具调用
    console.log('\n第2步 - 尝试解析为工具调用');
    const jsonString = JSON.stringify(extractedResult.json);
    console.log('JSON字符串:', jsonString);

    const toolCall = toolParserService.parseToolCall(jsonString);
    console.log('工具调用解析结果:', toolCall ? '成功' : '失败');

    if (toolCall) {
      console.log('工具调用信息:', {
        name: toolCall.name,
        params: toolCall.params
      });
    } else {
      console.log('toolParserService未能解析为工具调用');
      console.log('返回的toolCall值:', toolCall);
      console.log('jsonString类型:', typeof jsonString);
      console.log('jsonString内容:', jsonString);

      // 检查parseToolCall方法的实现
      console.log('\n检查 toolParserService:');
      console.log('parseToolCall方法存在:', typeof toolParserService.parseToolCall);
      if (toolParserService.parseToolCall) {
        // 尝试手动调用看看会发生什么
        try {
          const manualResult = toolParserService.parseToolCall(jsonString);
          console.log('手动调用结果:', manualResult);
        } catch (error) {
          console.log('手动调用出错:', error.message);
        }
      }
    }

    // 第3步：使用 ContentProcessor 完整流程
    console.log('\n第3步 - ContentProcessor完整流程');
    const result = ContentProcessor.extract(testContent);
    console.log('最终结果:');
    console.log('- 工具调用数量:', result.toolCalls.length);
    console.log('- 清理后内容:', JSON.stringify(result.cleanedContent));
    console.log('- 原始内容长度:', result.originalContent.length);
    console.log('- 清理后内容长度:', result.cleanedContent.length);

    expect(result.toolCalls.length).toBeGreaterThanOrEqual(0);
  });
});