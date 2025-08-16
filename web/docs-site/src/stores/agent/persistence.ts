import { type Ref } from 'vue';
import localforage from 'localforage';
import logger from '@/services/loggerService';
import type { Session } from './types';

// --- Localforage 和 debounce 设置 ---
const AGENT_CACHE_VERSION = '2.0';
export const sessionsStore = localforage.createInstance({ name: 'agentSessions' });
export const lastUsedRolesStore = localforage.createInstance({ name: 'lastUsedRoles' });

export async function forceClearAgentCache(): Promise<void> {
  await sessionsStore.clear();
  await lastUsedRolesStore.clear();
  logger.warn('[AgentStore] 缓存因数据过时或损坏已被清除。');
}

function debounce(func: (...args: any[]) => void, wait: number) {
  let timeout: number;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = window.setTimeout(later, wait);
  };
}

// --- Persistence 类型定义 ---
export interface PersistenceManager {
  initializeStoreFromCache(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): Promise<void>;
  persistState(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): () => void;
}

// --- Persistence 实现 ---
export class PersistenceManagerImpl implements PersistenceManager {
  async initializeStoreFromCache(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): Promise<void> {
    try {
      logger.log('[AgentStore] 正在从缓存初始化 store...');
      const cachedState = await sessionsStore.getItem<any>('state');
      
      if (!cachedState || cachedState.version !== AGENT_CACHE_VERSION) {
        logger.error(`[AgentStore] 检测到过时或损坏的缓存。正在清除缓存并重新开始。`, {
            foundVersion: cachedState?.version,
            expectedVersion: AGENT_CACHE_VERSION,
        });
        await forceClearAgentCache();
        
        sessions.value = {};
        activeSessionIds.value = { gi: null, hsr: null };

      } else {
        const { sessions: cachedSessions, activeSessionIds: cachedActiveIds } = cachedState.data;
        sessions.value = (typeof cachedSessions === 'object' && cachedSessions !== null) ? cachedSessions : {};
        logger.log(`[AgentStore] 已恢复 ${Object.keys(sessions.value).length} 个会话。`);
        
        const defaultIds = { gi: null, hsr: null };
        activeSessionIds.value = (typeof cachedActiveIds === 'object' && cachedActiveIds !== null)
                                 ? { ...defaultIds, ...cachedActiveIds }
                                 : defaultIds;
        logger.log('[AgentStore] 已恢复活动会话 ID。');
      }
      
    } catch (e) {
      logger.error('[AgentStore] 缓存初始化期间发生严重错误。正在清除缓存并重新开始。', e);
      await forceClearAgentCache();
      sessions.value = {};
      activeSessionIds.value = { gi: null, hsr: null };
    }
  }
  
  persistState(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): () => void {
    const persistFn = debounce(async () => {
      try {
        const stateToPersist = {
          version: AGENT_CACHE_VERSION,
          data: {
            sessions: JSON.parse(JSON.stringify(sessions.value)),
            activeSessionIds: JSON.parse(JSON.stringify(activeSessionIds.value)),
          }
        };
        await sessionsStore.setItem('state', stateToPersist);
        logger.log(`[AgentStore] 会话状态已持久化 (v${AGENT_CACHE_VERSION})。`);
      } catch (e) {
        logger.error('[AgentStore] 持久化状态失败:', e);
      }
    }, 1000);
    
    return persistFn;
  }
}