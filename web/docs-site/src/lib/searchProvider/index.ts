/**
 * SearchProvider 入口
 * 根据环境变量 VITE_SEARCH_MODE 决定使用本地搜索还是后端搜索
 *
 * - VITE_SEARCH_MODE=backend: 使用后端 Tantivy API
 * - VITE_SEARCH_MODE=local (默认): 使用前端本地搜索
 */

export type SearchMode = 'local' | 'backend';

export function getSearchMode(): SearchMode {
  const mode = import.meta.env.VITE_SEARCH_MODE;
  if (mode === 'backend') return 'backend';
  return 'local';
}

export function isBackendMode(): boolean {
  return getSearchMode() === 'backend';
}

export { type SearchProvider, type DocReadRequest, type DocSearchResult } from './types';
export { backendSearchProvider } from './backendProvider';
