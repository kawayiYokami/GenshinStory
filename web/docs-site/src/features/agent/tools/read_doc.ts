import { Tool, ToolExecutionResult } from './tool';
import localTools from '../services/localToolsService';
import { parseReadDocRequests } from '../services/toolParserService';
import logger from '../../app/services/loggerService';

interface ReadDocParams {
  args?: string;
}

const readDocTool: Tool<ReadDocParams> = {
  name: 'read_doc',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',
  prompt_trigger: undefined,

  async execute(params: ReadDocParams): Promise<ToolExecutionResult> {
    try {
      const docRequests = parseReadDocRequests(params.args ?? '');
      if (docRequests.length === 0) {
        return {
          result: "错误: 参数格式错误或缺失。请使用 'path' 或 'doc' 参数来指定要读取的文档。"
        };
      }

      const result = await localTools.readDoc(docRequests);
      return { result };

    } catch (error: any) {
      logger.error(`工具 read_doc 发生意外异常:`, error);
      return {
        result: `错误: 工具 'read_doc' 内部执行失败。请检查参数是否符合工具用法，或尝试其他方法。`
      };
    }
  }
};

export default readDocTool;