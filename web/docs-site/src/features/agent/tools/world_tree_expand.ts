import type { Tool, ToolExecutionResult } from './tool';
import logger from '@/features/app/services/loggerService';
import worldTreeQueryService from './implementations/worldTreeQueryService';

interface WorldTreeExpandToolParams {
  entityId?: string;
  entity_id?: string;
  relationTypes?: string[];
  relation_types?: string[];
  depth?: number;
  maxNodes?: number;
  max_nodes?: number;
  maxEdges?: number;
  max_edges?: number;
  includeRelatedFiles?: boolean;
  include_related_files?: boolean;
}

const worldTreeExpandTool: Tool<WorldTreeExpandToolParams> = {
  name: 'world_tree_expand',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: WorldTreeExpandToolParams): Promise<ToolExecutionResult> {
    try {
      const entityId = String(params.entity_id || params.entityId || '').trim();
      if (!entityId) {
        return { result: '错误: world_tree_expand 缺少 entity_id 参数。' };
      }

      const payload = {
        entity_id: entityId,
        relation_types: params.relation_types ?? params.relationTypes,
        depth: params.depth,
        max_nodes: params.max_nodes ?? params.maxNodes,
        max_edges: params.max_edges ?? params.maxEdges,
        include_related_files: params.include_related_files ?? params.includeRelatedFiles,
      };

      const response = await worldTreeQueryService.expand(payload as any);
      return {
        result: JSON.stringify({
          tool: 'world_tree_expand',
          ...response,
        }, null, 2),
      };
    } catch (error: any) {
      logger.error("工具 world_tree_expand 发生意外异常:", error);
      return {
        result: "错误: 工具 'world_tree_expand' 内部执行失败。",
      };
    }
  },
};

export default worldTreeExpandTool;

