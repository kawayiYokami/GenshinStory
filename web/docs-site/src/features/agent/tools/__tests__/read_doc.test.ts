import { describe, it, expect } from 'vitest';
import readDocTool, { ReadDocParams } from '../../tools/read_doc';

describe('read_doc 工具测试', () => {
  describe('参数处理', () => {
    it('应该能处理简单的 path 参数', async () => {
      const params = {
        path: 'test.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      // 由于实际文件不存在，会返回文件未找到错误，而不是参数格式错误
      expect(result.result).not.toContain('参数格式错误或缺失');
    });

    it('应该能处理 args 对象参数', async () => {
      const params = {
        args: {
          doc: {
            path: 'test.md'
          }
        }
      };

      const result = await readDocTool.execute(params);

      expect(result.result).not.toContain('参数格式错误或缺失');
    });

    it('应该能处理直接的 path 对象', async () => {
      const params = {
        path: 'books/月份篇-190742.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      expect(result.result).not.toContain('参数格式错误或缺失');
    });

    it('应该能处理嵌套的 args 结构', async () => {
      const params = {
        args: {
          doc: {
            path: 'character/璃月港/钟离-10000030.md',
            line_range: ['1-50']
          }
        }
      };

      const result = await readDocTool.execute(params);

      expect(result.result).not.toContain('参数格式错误或缺失');
    });

    it('应该处理空参数', async () => {
      const params = {};

      const result = await readDocTool.execute(params);

      expect(result.result).toContain('参数格式错误或缺失');
    });

    it('应该处理无效的参数结构', async () => {
      const params = {
        invalid: 'parameter'
      } as any;

      const result = await readDocTool.execute(params);

      expect(result.result).toContain('参数格式错误或缺失');
    });
  });
});