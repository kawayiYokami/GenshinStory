import type { Tool, ToolExecutionResult } from './tool';
import logger from '@/features/app/services/loggerService';
import worldTreeQueryService from './implementations/worldTreeQueryService';

interface WorldTreePathsToolParams {
  fromEntityId?: string;
  from_entity_id?: string;
  toEntityId?: string;
  to_entity_id?: string;
  maxDepth?: number;
  max_depth?: number;
  maxPaths?: number;
  max_paths?: number;
}

const worldTreePathsTool: Tool<WorldTreePathsToolParams> = {
  name: 'world_tree_paths',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: WorldTreePathsToolParams): Promise<ToolExecutionResult> {
    try {
      const fromEntityId = String(params.from_entity_id || params.fromEntityId || '').trim();
      const toEntityId = String(params.to_entity_id || params.toEntityId || '').trim();

      if (!fromEntityId || !toEntityId) {
        return { result: '错误: world_tree_paths 缺少 from_entity_id 或 to_entity_id 参数。' };
      }

      const payload = {
        from_entity_id: fromEntityId,
        to_entity_id: toEntityId,
        max_depth: params.max_depth ?? params.maxDepth,
        max_paths: params.max_paths ?? params.maxPaths,
      };

      const response = await worldTreeQueryService.paths(payload as any);
      return {
        result: JSON.stringify({
          tool: 'world_tree_paths',
          ...response,
        }, null, 2),
      };
    } catch (error: any) {
      logger.error("工具 world_tree_paths 发生意外异常:", error);
      return {
        result: "错误: 工具 'world_tree_paths' 内部执行失败。",
      };
    }
  },
};

export default worldTreePathsTool;

