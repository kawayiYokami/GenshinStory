import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest';
import readDocTool, { ReadDocParams } from '../../tools/read_doc';
import localTools from '../../services/localToolsService';
import { parseReadDocRequests } from '../../services/toolParserService';

// Mock the dependencies
vi.mock('../../services/localToolsService', () => ({
  default: {
    readDoc: vi.fn()
  }
}));

vi.mock('../../services/toolParserService', () => ({
  parseReadDocRequests: vi.fn()
}));

vi.mock('../../app/services/loggerService', () => ({
  default: {
    error: vi.fn(),
    log: vi.fn()
  }
}));

describe('read_doc 工具增强测试', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Restore all mocks after each test
    vi.restoreAllMocks();
  });

  describe('参数处理', () => {
    it('应该能处理简单的 path 参数', async () => {
      console.log('测试: 处理简单的 path 参数');

      // Mock the parser to return a valid request
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'test.md', lineRanges: [] }
      ]);

      // Mock the localTools to return a successful result
      (localTools.readDoc as Mock).mockResolvedValue(
        '<docs><doc><path>test.md</path><content><![CDATA[测试内容]]></content></doc></docs>'
      );

      const params = {
        path: 'test.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证解析器被正确调用
      expect(parseReadDocRequests).toHaveBeenCalledWith(JSON.stringify({ doc: { path: 'test.md' } }));

      // 验证本地工具被正确调用
      expect(localTools.readDoc).toHaveBeenCalledWith([
        { path: 'test.md', lineRanges: [] }
      ]);

      // 验证结果不包含参数格式错误
      expect(result.result).not.toContain('参数格式错误或缺失');

      console.log('测试通过: 处理简单的 path 参数');
    });

    it('应该能处理 args 对象参数', async () => {
      console.log('测试: 处理 args 对象参数');

      // Mock the parser to return a valid request
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'test.md', lineRanges: [] }
      ]);

      // Mock the localTools to return a successful result
      (localTools.readDoc as Mock).mockResolvedValue(
        '<docs><doc><path>test.md</path><content><![CDATA[测试内容]]></content></doc></docs>'
      );

      const params = {
        args: {
          doc: {
            path: 'test.md'
          }
        }
      };

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证解析器被正确调用
      expect(parseReadDocRequests).toHaveBeenCalledWith(JSON.stringify(params.args));

      // 验证本地工具被正确调用
      expect(localTools.readDoc).toHaveBeenCalledWith([
        { path: 'test.md', lineRanges: [] }
      ]);

      // 验证结果不包含参数格式错误
      expect(result.result).not.toContain('参数格式错误或缺失');

      console.log('测试通过: 处理 args 对象参数');
    });

    it('应该能处理直接的 path 对象', async () => {
      console.log('测试: 处理直接的 path 对象');

      // Mock the parser to return a valid request
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'books/月份篇-190742.md', lineRanges: [] }
      ]);

      // Mock the localTools to return a successful result
      (localTools.readDoc as Mock).mockResolvedValue(
        '<docs><doc><path>books/月份篇-190742.md</path><content><![CDATA[测试内容]]></content></doc></docs>'
      );

      const params = {
        path: 'books/月份篇-190742.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证解析器被正确调用
      expect(parseReadDocRequests).toHaveBeenCalledWith(JSON.stringify({ doc: { path: 'books/月份篇-190742.md' } }));

      // 验证本地工具被正确调用
      expect(localTools.readDoc).toHaveBeenCalledWith([
        { path: 'books/月份篇-190742.md', lineRanges: [] }
      ]);

      // 验证结果不包含参数格式错误
      expect(result.result).not.toContain('参数格式错误或缺失');

      console.log('测试通过: 处理直接的 path 对象');
    });

    it('应该能处理嵌套的 args 结构', async () => {
      console.log('测试: 处理嵌套的 args 结构');

      // Mock the parser to return a valid request
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'character/璃月港/钟离-10000030.md', lineRanges: ['1-50'] }
      ]);

      // Mock the localTools to return a successful result
      (localTools.readDoc as Mock).mockResolvedValue(
        '<docs><doc><path>character/璃月港/钟离-10000030.md</path><content lines="1-50"><![CDATA[测试内容]]></content></doc></docs>'
      );

      const params = {
        args: {
          doc: {
            path: 'character/璃月港/钟离-10000030.md',
            line_range: ['1-50']
          }
        }
      };

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证解析器被正确调用
      expect(parseReadDocRequests).toHaveBeenCalledWith(JSON.stringify(params.args));

      // 验证本地工具被正确调用
      expect(localTools.readDoc).toHaveBeenCalledWith([
        { path: 'character/璃月港/钟离-10000030.md', lineRanges: ['1-50'] }
      ]);

      // 验证结果不包含参数格式错误
      expect(result.result).not.toContain('参数格式错误或缺失');

      console.log('测试通过: 处理嵌套的 args 结构');
    });

    it('应该处理空参数', async () => {
      console.log('测试: 处理空参数');

      // Mock the parser to return an empty array for empty params
      (parseReadDocRequests as Mock).mockReturnValue([]);

      const params = {};

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证解析器被调用
      expect(parseReadDocRequests).toHaveBeenCalledWith(JSON.stringify(params));

      // 验证结果包含参数格式错误
      expect(result.result).toContain('参数格式错误或缺失');

      console.log('测试通过: 处理空参数');
    });

    it('应该处理无效的参数结构', async () => {
      console.log('测试: 处理无效的参数结构');

      // Mock the parser to return an empty array for invalid params
      (parseReadDocRequests as Mock).mockReturnValue([]);

      const params = {
        invalid: 'parameter'
      } as any;

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证解析器被调用
      expect(parseReadDocRequests).toHaveBeenCalledWith(JSON.stringify(params));

      // 验证结果包含参数格式错误
      expect(result.result).toContain('参数格式错误或缺失');

      console.log('测试通过: 处理无效的参数结构');
    });
  });

  describe('错误处理', () => {
    it('应该处理解析器错误', async () => {
      console.log('测试: 处理解析器错误');

      // Mock the parser to throw an error
      (parseReadDocRequests as Mock).mockImplementation(() => {
        throw new Error('解析错误');
      });

      const params = {
        path: 'test.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证结果包含错误信息
      expect(result.result).toContain('工具 \'read_doc\' 内部执行失败');

      console.log('测试通过: 处理解析器错误');
    });

    it('应该处理本地工具错误', async () => {
      console.log('测试: 处理本地工具错误');

      // Mock the parser to return a valid request
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'test.md', lineRanges: [] }
      ]);

      // Mock the localTools to throw an error
      (localTools.readDoc as Mock).mockRejectedValue(new Error('本地工具错误'));

      const params = {
        path: 'test.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证结果包含错误信息
      expect(result.result).toContain('工具 \'read_doc\' 内部执行失败');

      console.log('测试通过: 处理本地工具错误');
    });
  });

  describe('结果处理', () => {
    it('应该正确处理单个文档的结果', async () => {
      console.log('测试: 处理单个文档的结果');

      // Mock the parser to return a valid request
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'test.md', lineRanges: [] }
      ]);

      // Mock the localTools to return a successful result
      (localTools.readDoc as Mock).mockResolvedValue(
        '<docs><doc><path>test.md</path><content><![CDATA[测试内容]]></content></doc></docs>'
      );

      const params = {
        path: 'test.md'
      } as ReadDocParams;

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证结果包含正确的后续提示
      expect(result.followUpPrompt).toBe('感谢你帮我读取了文档。请先对刚才读取的文档内容做一个简要的总结和汇报，然后告诉我是否可以继续进行下一步分析。');

      console.log('测试通过: 处理单个文档的结果');
    });

    it('应该正确处理多个文档的结果', async () => {
      console.log('测试: 处理多个文档的结果');

      // Mock the parser to return multiple requests
      (parseReadDocRequests as Mock).mockReturnValue([
        { path: 'test1.md', lineRanges: [] },
        { path: 'test2.md', lineRanges: [] }
      ]);

      // Mock the localTools to return a successful result
      (localTools.readDoc as Mock).mockResolvedValue(
        '<docs><doc><path>test1.md</path><content><![CDATA[测试内容1]]></content></doc><doc><path>test2.md</path><content><![CDATA[测试内容2]]></content></doc></docs>'
      );

      const params = {
        args: {
          docs: [
            { path: 'test1.md' },
            { path: 'test2.md' }
          ]
        }
      };

      const result = await readDocTool.execute(params);

      console.log('执行结果:', result);

      // 验证结果包含正确的后续提示
      expect(result.followUpPrompt).toBe('感谢你帮我读取了这 2 个文档。请先对读取的文档内容做一个简要的总结和汇报，然后询问我是否可以进行下一步的分析工作。');

      console.log('测试通过: 处理多个文档的结果');
    });
  });
});