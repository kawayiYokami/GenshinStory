import type { Tool, ToolExecutionResult } from './tool';
import logger from '@/features/app/services/loggerService';
import worldTreeQueryService from './implementations/worldTreeQueryService';

interface WorldTreeQueryToolParams {
  query?: string;
  intent?: 'entity' | 'relationship' | 'event' | 'timeline' | 'theme' | 'analysis';
  entities?: string[];
  maxFiles?: number;
  max_files?: number;
  maxRelations?: number;
  max_relations?: number;
  maxEntities?: number;
  max_entities?: number;
  maxEvents?: number;
  max_events?: number;
  maxChunksPerFile?: number;
  max_chunks_per_file?: number;
  includeQuotes?: boolean;
  include_quotes?: boolean;
}

const worldTreeQueryTool: Tool<WorldTreeQueryToolParams> = {
  name: 'world_tree_query',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: WorldTreeQueryToolParams): Promise<ToolExecutionResult> {
    try {
      const query = String(params.query || '').trim();
      if (!query) {
        return { result: '错误: world_tree_query 缺少 query 参数。' };
      }

      const payload = {
        query,
        intent: params.intent,
        entities: Array.isArray(params.entities) ? params.entities.filter(Boolean) : undefined,
        max_files: params.max_files ?? params.maxFiles,
        max_relations: params.max_relations ?? params.maxRelations,
        max_entities: params.max_entities ?? params.maxEntities,
        max_events: params.max_events ?? params.maxEvents,
        max_chunks_per_file: params.max_chunks_per_file ?? params.maxChunksPerFile,
        include_quotes: params.include_quotes ?? params.includeQuotes,
      };

      const response = await worldTreeQueryService.query(payload as any);

      return {
        result: JSON.stringify({
          tool: 'world_tree_query',
          ...response,
        }, null, 2),
      };
    } catch (error: any) {
      logger.error("工具 world_tree_query 发生意外异常:", error);
      return {
        result: "错误: 工具 'world_tree_query' 内部执行失败。",
      };
    }
  },
};

export default worldTreeQueryTool;

