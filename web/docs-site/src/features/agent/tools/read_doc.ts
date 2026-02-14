import type { Tool, ToolExecutionResult } from './tool';
import localTools from './implementations/localToolsService';
import logger from '../../app/services/loggerService';

export interface ReadDocParams {
  args?: any;
  path?: string;
  line_range?: string;
}

const readDocTool: Tool<ReadDocParams> = {
  name: 'read_doc',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: ReadDocParams): Promise<ToolExecutionResult> {
    try {
      // 直接使用 JsonParserService 解析后的参数
      const docPath = params.path;
      const lineRange = params.line_range;

      if (!docPath) {
        return {
          result: "错误：缺失必需的 path 参数。请指定要读取的文档路径。"
        };
      }

      const result = await localTools.readDoc([{
        path: docPath,
        lineRanges: lineRange ? [lineRange] : []
      }]);

      // 单文件读取，不需要复杂逻辑
      const followUpPrompt = "感谢你帮我读取了文档。请先对刚才读取的文档内容做一个简要的总结和汇报，然后告诉我是否可以继续进行下一步分析。";

      return {
        result,
        followUpPrompt
      };

    } catch (error: any) {
      logger.error(`工具 read_doc 发生意外异常:`, error);
      return {
        result: `错误: 工具 'read_doc' 内部执行失败。请检查参数是否符合工具用法，或尝试其他方法。`
      };
    }
  }
};

export default readDocTool;
