import { Tool, ToolExecutionResult } from './tool';
import localTools from '../services/localToolsService';
import logger from '../../app/services/loggerService';

interface ListDocsParams {
  path?: string;
}

const listDocsTool: Tool<ListDocsParams> = {
  name: 'list_docs',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',
  prompt_trigger: undefined,

  async execute(params: ListDocsParams): Promise<ToolExecutionResult> {
    try {
      const path = params.path || '/';

      const result = await localTools.listDocs(path);
      return { result };

    } catch (error: any) {
      logger.error(`工具 list_docs 发生意外异常:`, error);
      return {
        result: `错误: 工具 'list_docs' 内部执行失败。请检查参数是否符合工具用法，或尝试其他方法。`
      };
    }
  }
};

export default listDocsTool;