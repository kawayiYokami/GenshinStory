import { describe, it, expect } from 'vitest';
import { cleanContentFromToolCalls, type ToolCall } from '../../utils/messageUtils';

// 测试数据
const mockToolCalls = [
  {
    name: 'read_doc',
    params: { path: 'test.md' },
    original: '<read_doc>\n  <path>test.md</path>\n</read_doc>'
  }
];

describe('MessageBubble 工具调用内容清洗', () => {
  it('应该从内容中移除工具调用 XML', () => {
    const content = '这是消息内容\n<read_doc>\n  <path>test.md</path>\n</read_doc>\n这是后续内容';
    
    const cleaned = cleanContentFromToolCalls(content, mockToolCalls);
    
    expect(cleaned).toBe('这是消息内容\n这是后续内容');
  });

  it('应该处理只有工具调用的情况', () => {
    const content = '<read_doc>\n  <path>test.md</path>\n</read_doc>';
    
    const cleaned = cleanContentFromToolCalls(content, mockToolCalls);
    
    expect(cleaned).toBe('');
  });

  it('应该处理没有工具调用的情况', () => {
    const content = '这是普通消息内容';
    
    const cleaned = cleanContentFromToolCalls(content, []);
    
    expect(cleaned).toBe('这是普通消息内容');
  });

  it('应该处理 undefined tool_calls', () => {
    const content = '这是普通消息内容';
    
    const cleaned = cleanContentFromToolCalls(content, undefined);
    
    expect(cleaned).toBe('这是普通消息内容');
  });

  it('应该处理多个工具调用', () => {
    const toolCalls = [
      ...mockToolCalls,
      {
        name: 'search_docs',
        params: { query: 'test' },
        original: '<search_docs>\n  <query>test</query>\n</search_docs>'
      }
    ];
    
    const content = '内容1\n<read_doc>\n  <path>test.md</path>\n</read_doc>\n内容2\n<search_docs>\n  <query>test</query>\n</search_docs>\n内容3';
    
    const cleaned = cleanContentFromToolCalls(content, toolCalls);
    
    expect(cleaned).toBe('内容1\n内容2\n内容3');
  });

  it('应该处理带有特殊字符的 XML', () => {
    const toolCalls = [
      {
        name: 'read_doc',
        params: { path: 'file with spaces.md' },
        original: '<read_doc>\n  <path>file with spaces.md</path>\n</read_doc>'
      }
    ];
    
    const content = '查看文件：<read_doc>\n  <path>file with spaces.md</path>\n</read_doc>';
    
    const cleaned = cleanContentFromToolCalls(content, toolCalls);
    
    expect(cleaned).toBe('查看文件：');
  });
});