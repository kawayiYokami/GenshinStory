import { Tool, ToolExecutionResult } from './tool';
import logger from '../../app/services/loggerService';

interface AskParams {
  question?: string;
  suggest?: string | string[];
}

const askTool: Tool<AskParams> = {
  name: 'ask',
  type: 'ui',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',
  prompt_trigger: undefined,

  async execute(params: AskParams): Promise<ToolExecutionResult> {
    try {
      const question = params.question || '未提供问题';
      const suggestions = params.suggest ? [params.suggest].flat() : [];
      
      if (!question || suggestions.length < 2) {
        return {
          result: "错误: 参数不完整。'ask' 工具需要明确的 'question' 和至少2个 'suggest' 选项。"
        };
      }

      // ask 工具不需要后端执行，直接返回用户提问格式
      let result = `用户提问: ${question}`;
      if (suggestions.length > 0) {
        result += `\n建议选项: ${suggestions.join(', ')}`;
      }

      return { result };

    } catch (error: any) {
      logger.error(`工具 ask 发生意外异常:`, error);
      return {
        result: `错误: 工具 'ask' 内部执行失败。请检查参数是否符合工具用法，或尝试其他方法。`
      };
    }
  }
};

export default askTool;