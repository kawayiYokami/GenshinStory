import { isBackendMode } from '@/lib/searchProvider';
import { useAppStore } from '@/features/app/stores/app';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '/api';
const API_BASE = BACKEND_URL.endsWith('/api') ? BACKEND_URL : `${BACKEND_URL}/api`;

export interface WorldTreeQueryParams {
  query: string;
  intent?: 'entity' | 'relationship' | 'event' | 'timeline' | 'theme' | 'analysis';
  entities?: string[];
  max_entities?: number;
  max_relations?: number;
  max_events?: number;
  max_files?: number;
  max_chunks_per_file?: number;
  include_quotes?: boolean;
}

export interface WorldTreeExpandParams {
  entity_id: string;
  relation_types?: string[];
  depth?: number;
  max_nodes?: number;
  max_edges?: number;
  include_related_files?: boolean;
}

export interface WorldTreePathsParams {
  from_entity_id: string;
  to_entity_id: string;
  max_depth?: number;
  max_paths?: number;
}

export interface WorldTreeImportGraphItem {
  id?: string;
  domain?: string;
  file_path: string;
  chunk_id: string;
  title?: string;
  judgment?: string;
  reasoning?: string;
  entities?: Array<{
    name: string;
    type: string;
    aliases?: string[];
    summary?: string;
  }>;
  relations?: Array<{
    subject: string;
    predicate: string;
    object: string;
    confidence?: number;
    reason?: string;
    evidence: {
      file_path: string;
      chunk_id: string;
      quote?: string;
    };
  }>;
  events?: Array<{
    name: string;
    type?: string;
    summary?: string;
    participants?: string[];
    confidence?: number;
    evidence: {
      file_path: string;
      chunk_id: string;
      quote?: string;
    };
  }>;
  notes?: string[];
}

export interface WorldTreeImportGraphParams {
  items: WorldTreeImportGraphItem[];
  dry_run?: boolean;
}

interface WorldTreeError {
  error: string;
  message: string;
}

class WorldTreeQueryService {
  public isEnabled(): boolean {
    return isBackendMode();
  }

  private async post<TPayload extends Record<string, any>>(endpoint: string, payload: TPayload): Promise<any | WorldTreeError> {
    if (!this.isEnabled()) {
      return {
        error: 'WORLD_TREE_DISABLED',
        message: '当前未启用后端模式，世界树查询不可用。',
      };
    }

    const appStore = useAppStore();
    const domain = appStore.currentDomain || 'gi';

    try {
      const response = await fetch(`${API_BASE}/world-tree/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...payload,
          domain,
        }),
      });

      if (!response.ok) {
        const detail = await response.text();
        return {
          error: 'WORLD_TREE_REQUEST_FAILED',
          message: `世界树接口请求失败: ${response.status} ${detail || response.statusText}`,
        };
      }

      return await response.json();
    } catch (error: any) {
      return {
        error: 'WORLD_TREE_INTERNAL_ERROR',
        message: `世界树接口调用异常: ${error?.message || String(error)}`,
      };
    }
  }

  public async query(params: WorldTreeQueryParams): Promise<any | WorldTreeError> {
    return this.post('query', params as Record<string, any>);
  }

  public async expand(params: WorldTreeExpandParams): Promise<any | WorldTreeError> {
    return this.post('expand', params as Record<string, any>);
  }

  public async paths(params: WorldTreePathsParams): Promise<any | WorldTreeError> {
    return this.post('paths', params as Record<string, any>);
  }

  public async importGraph(params: WorldTreeImportGraphParams): Promise<any | WorldTreeError> {
    return this.post('import-graph', params as Record<string, any>);
  }
}

export const worldTreeQueryService = new WorldTreeQueryService();
export default worldTreeQueryService;
