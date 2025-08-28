import { describe, it, expect } from 'vitest';
import { convertParams } from '../toolParserService';

describe('convertParams 参数转换', () => {
  describe('read_doc 工具', () => {
    it('应该为 read_doc 工具保留 args 参数的对象结构', () => {
      const params = {
        args: {
          doc: {
            path: 'test.md',
            line_range: ['1-10']
          }
        }
      };

      const result = convertParams('read_doc', params);
      
      expect(result.args).toEqual({
        doc: {
          path: 'test.md',
          line_range: ['1-10']
        }
      });
      expect(typeof result.args).toBe('object');
    });

    it('应该为 read_doc 工具只保留 args 参数的对象结构', () => {
      const params = {
        args: {
          doc: {
            path: 'test.md'
          }
        },
        metadata: {
          chapter: 1,
          section: 'intro'
        },
        query: 'test query'
      };

      const result = convertParams('read_doc', params);
      
      expect(result.args).toEqual({
        doc: {
          path: 'test.md'
        }
      });
      expect(typeof result.args).toBe('object');
      expect(result.metadata).toBe('{"chapter":1,"section":"intro"}');
      expect(result.query).toBe('test query');
    });

    it('应该处理 read_doc 工具的混合参数类型', () => {
      const params = {
        args: { path: 'test.md' },
        simpleString: 'hello',
        number: 42,
        complex: { nested: true }
      };

      const result = convertParams('read_doc', params);
      
      expect(result.args).toEqual({ path: 'test.md' });
      expect(result.simpleString).toBe('hello');
      expect(result.number).toBe(42);
      expect(result.complex).toBe('{"nested":true}');
    });
  });

  describe('search_docs 工具', () => {
    it('应该将 search_docs 工具的对象参数转换为字符串', () => {
      const params = {
        query: { type: 'regex', pattern: 'test.*' },
        filter: { category: 'docs' }
      };

      const result = convertParams('search_docs', params);
      
      expect(result.query).toBe('{"type":"regex","pattern":"test.*"}');
      expect(result.filter).toBe('{"category":"docs"}');
    });

    it('应该保留 search_docs 工具的字符串参数', () => {
      const params = {
        query: 'simple search',
        limit: 10
      };

      const result = convertParams('search_docs', params);
      
      expect(result.query).toBe('simple search');
      expect(result.limit).toBe('10');
    });
  });

  describe('list_docs 工具', () => {
    it('应该将 list_docs 工具的对象参数转换为字符串', () => {
      const params = {
        path: { base: '/docs', recursive: true },
        format: 'json'
      };

      const result = convertParams('list_docs', params);
      
      expect(result.path).toBe('{"base":"/docs","recursive":true}');
      expect(result.format).toBe('json');
    });
  });

  describe('ask 工具', () => {
    it('应该将 ask 工具的对象参数转换为字符串', () => {
      const params = {
        question: { text: 'What is this?', context: 'docs' },
        suggest: ['yes', 'no']
      };

      const result = convertParams('ask', params);
      
      expect(result.question).toBe('{"text":"What is this?","context":"docs"}');
      expect(result.suggest).toBe('["yes","no"]');
    });
  });

  describe('默认行为', () => {
    it('应该为未知工具使用默认转换逻辑', () => {
      const params = {
        stringParam: 'hello',
        objectParam: { key: 'value' },
        numberParam: 42
      };

      const result = convertParams('unknown_tool', params);
      
      expect(result.stringParam).toBe('hello');
      expect(result.objectParam).toBe('{"key":"value"}');
      expect(result.numberParam).toBe('42');
    });
  });

  describe('边界情况', () => {
    it('应该处理空参数对象', () => {
      const result = convertParams('read_doc', {});
      expect(result).toEqual({});
    });

    it('应该处理 null 和 undefined 值', () => {
      const params = {
        nullValue: null,
        undefinedValue: undefined,
        stringValue: 'test'
      };

      const result = convertParams('read_doc', params);
      
      expect(result.nullValue).toBe('null');
      expect(result.undefinedValue).toBe('undefined');
      expect(result.stringValue).toBe('test');
    });

    it('应该处理数组和嵌套对象', () => {
      const params = {
        array: [1, 2, { nested: true }],
        nested: { level1: { level2: 'deep' } }
      };

      const result = convertParams('search_docs', params);
      
      expect(result.array).toBe('[1,2,{"nested":true}]');
      expect(result.nested).toBe('{"level1":{"level2":"deep"}}');
    });
  });
});