import { Tool, ToolExecutionResult } from './tool';
import localTools from '../services/localToolsService';
import { parseReadDocRequests } from '../services/toolParserService';
import logger from '../../app/services/loggerService';

export interface ReadDocParams {
  args?: any;
  path?: string;
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
      let argsContent: string;

      if (typeof params.args === 'string') {
        argsContent = params.args;
      } else if (params.args && typeof params.args === 'object') {
        // 如果 args 是对象，转换为 JSON 字符串
        argsContent = JSON.stringify(params.args);
      } else if (params.path) {
        // 如果有直接的 path 参数，包装成 doc 对象
        argsContent = JSON.stringify({ doc: { path: params.path } });
      } else {
        // 尝试解析整个参数对象
        argsContent = JSON.stringify(params);
      }

      const docRequests = parseReadDocRequests(argsContent);
      if (docRequests.length === 0) {
        return {
          result: "错误: 参数格式错误或缺失。请使用 'path' 或 'doc' 参数来指定要读取的文档。"
        };
      }

      const result = await localTools.readDoc(docRequests);

      // 根据读取的文档数量生成不同的阶段性汇报提示
      let followUpPrompt: string | undefined;

      if (docRequests.length === 1) {
        followUpPrompt = "感谢你帮我读取了文档。请先对刚才读取的文档内容做一个简要的总结和汇报，然后告诉我是否可以继续进行下一步分析。";
      } else if (docRequests.length > 1) {
        followUpPrompt = `感谢你帮我读取了这 ${docRequests.length} 个文档。请先对读取的文档内容做一个简要的总结和汇报，然后询问我是否可以进行下一步的分析工作。`;
      }

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