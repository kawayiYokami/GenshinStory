import { Tool, ToolExecutionResult } from './tool';
import localTools from '../services/localToolsService';
import logger from '../../app/services/loggerService';

interface SearchDocsParams {
  query?: string;
  path?: string;
  regex?: string;
  args?: string;
}

const searchDocsTool: Tool<SearchDocsParams> = {
  name: 'search_docs',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: SearchDocsParams): Promise<ToolExecutionResult> {
    try {
      const query = params.query || params.regex || params.args;
      if (!query) {
        return {
          result: "错误: 参数缺失。请在调用 'search_docs' 时提供 'query' 或 'regex' 参数。"
        };
      }

      const result = await localTools.searchDocs(query, params.path, {
        maxResults: 50,
        generateSummary: true
      });
      return { result };

    } catch (error: any) {
      logger.error(`工具 search_docs 发生意外异常:`, error);
      return {
        result: `错误: 工具 'search_docs' 内部执行失败。请检查参数是否符合工具用法，或尝试其他方法。`
      };
    }
  }
};

export default searchDocsTool;