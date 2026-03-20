import type { Tool, ToolExecutionResult } from './tool';
import localTools from './implementations/localToolsService';
import logger from '../../app/services/loggerService';

interface ResolveSourceLinkParams {
  title?: string;
  path?: string;
  fileName?: string;
  query?: string;
  args?: string;
  k?: number;
  minScore?: number;
}

const resolveSourceLinkTool: Tool<ResolveSourceLinkParams> = {
  name: 'resolve_source_link',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: ResolveSourceLinkParams): Promise<ToolExecutionResult> {
    try {
      const title = params.title || params.path || params.fileName || params.query || params.args;
      if (!title || !String(title).trim()) {
        return {
          result: "错误: 参数缺失。请在调用 'resolve_source_link' 时提供 title（可传文件名或相对路径）。"
        };
      }

      const k = Math.min(Math.max(1, Number(params.k ?? 3)), 10);
      const minScore = Math.min(Math.max(0, Number(params.minScore ?? 100)), 1000);
      const result = await localTools.resolveSourceLink(String(title), { k, minScore });
      return { result };
    } catch (error: any) {
      logger.error(`工具 resolve_source_link 发生意外异常:`, error);
      return {
        result: "错误: 工具 'resolve_source_link' 内部执行失败。请检查参数后重试。"
      };
    }
  }
};

export default resolveSourceLinkTool;
