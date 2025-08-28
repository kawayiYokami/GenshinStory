import { describe, it, expect } from 'vitest';
import parserAdapter from '../../services/parserAdapter';

describe('工具调用鲁棒性测试', () => {
  describe('工具名称别名映射', () => {
    it('应该能将 read_file 映射为 read_doc', () => {
      const xml = '<read_file><path>test.md</path></read_file>';
      const result = parserAdapter.parseSingleToolCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.name).toBe('read_doc');
      expect(result?.params.path).toBe('test.md');
    });

    it('应该能将 search 映射为 search_docs', () => {
      const xml = '<search><query>Vue 3</query></search>';
      const result = parserAdapter.parseSingleToolCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.name).toBe('search_docs');
      expect(result?.params.query).toBe('Vue 3');
    });

    it('应该能将 ls 映射为 list_docs', () => {
      const xml = '<ls><path>/docs</path></ls>';
      const result = parserAdapter.parseSingleToolCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.name).toBe('list_docs');
      expect(result?.params.path).toBe('/docs');
    });

    it('应该拒绝无效的工具名称', () => {
      const xml = '<invalid_tool><param>value</param></invalid_tool>';
      const result = parserAdapter.parseSingleToolCall(xml);
      
      expect(result).toBeNull();
    });
  });

  describe('ask 工具参数处理', () => {
    it('应该自动补全缺失的 question', () => {
      const xml = '<ask><suggest>选项1</suggest><suggest>选项2</suggest></ask>';
      const result = parserAdapter.parseAskCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.question).toBe('请选择');
      expect(result?.suggestions).toEqual(['选项1', '选项2']);
    });

    it('应该限制过多的建议为4个', () => {
      const xml = `
        <ask>
          <question>选择一个选项</question>
          <suggest>选项1</suggest>
          <suggest>选项2</suggest>
          <suggest>选项3</suggest>
          <suggest>选项4</suggest>
          <suggest>选项5</suggest>
          <suggest>选项6</suggest>
        </ask>
      `;
      const result = parserAdapter.parseAskCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.suggestions).toHaveLength(4);
      expect(result?.suggestions).toEqual(['选项1', '选项2', '选项3', '选项4']);
    });

    it('应该能处理 suggestions 字段', () => {
      const xml = `
        <ask>
          <question>选择一个选项</question>
          <suggestions>选项1</suggestions>
          <suggestions>选项2</suggestions>
        </ask>
      `;
      const result = parserAdapter.parseAskCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.suggestions).toEqual(['选项1', '选项2']);
    });

    it('应该处理没有建议的情况', () => {
      const xml = '<ask><question>确定要继续吗？</question></ask>';
      const result = parserAdapter.parseAskCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.question).toBe('确定要继续吗？');
      expect(result?.suggestions).toEqual([]);
    });
  });

  describe('综合鲁棒性测试', () => {
    it('应该能处理别名工具和参数问题的组合', () => {
      const xml = `
        <open>
          <args>
            <doc>
              <path>复杂文档.md</path>
            </doc>
          </args>
        </open>
      `;
      const result = parserAdapter.parseSingleToolCall(xml);
      
      expect(result).toBeTruthy();
      expect(result?.name).toBe('read_doc');
      expect(result?.params.args).toBeTruthy();
    });
  });
});