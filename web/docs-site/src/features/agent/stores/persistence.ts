import { type Ref } from 'vue';
import logger from '@/features/app/services/loggerService';
import type { Session } from '../types';
import { sessionsStore, lastUsedRolesStore } from '@/features/app/services/storageFacade';
export { sessionsStore, lastUsedRolesStore };

// --- Localforage 和 debounce 设置 ---
const AGENT_CACHE_VERSION = '2.0';

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

function ensureSessionMessageIntegrity(session: Session): void {
  if (!session.messagesById || typeof session.messagesById !== 'object') {
    session.messagesById = {};
  }
  if (!Array.isArray(session.messageIds)) {
    session.messageIds = [];
  }

  const sourceMessagesById = session.messagesById as Record<string, any>;
  const seenIds = new Set<string>();
  const normalizedIds: string[] = [];
  const normalizedMessagesById: Record<string, any> = {};
  const fallbackCreatedAt = session.createdAt || new Date().toISOString();

  const attachMessage = (id: string, message: any) => {
    if (!id || seenIds.has(id)) return;
    if (!message || typeof message !== 'object') return;

    seenIds.add(id);
    if (message.id !== id) {
      message.id = id;
    }
    if (typeof message.createdAt !== 'string' || !message.createdAt) {
      message.createdAt = fallbackCreatedAt;
    }
    normalizedIds.push(id);
    normalizedMessagesById[id] = message;
  };

  for (const rawId of session.messageIds) {
    if (typeof rawId !== 'string' || !rawId.trim()) continue;
    const id = rawId.trim();
    attachMessage(id, sourceMessagesById[id]);
  }

  for (const [id, message] of Object.entries(sourceMessagesById)) {
    attachMessage(id, message);
  }

  session.messageIds = normalizedIds;
  session.messagesById = normalizedMessagesById;
}

// --- Persistence 类型定义 ---
export interface PersistenceManager {
  initializeStoreFromCache(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>, activeInstructionId: Ref<string>): Promise<void>;
  persistState(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>, activeInstructionId: Ref<string>): () => void;
}

// --- Persistence 实现 ---
export class PersistenceManagerImpl implements PersistenceManager {
  async initializeStoreFromCache(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>, activeInstructionId: Ref<string>): Promise<void> {
    try {
      logger.log('[AgentStore] 正在从缓存初始化 store...');
      const cachedState = await sessionsStore.getItem<any>('state');

      // 移除版本检查，保护用户历史数据不被清空
      if (!cachedState) {
        logger.log('[AgentStore] 没有找到缓存数据，使用空状态开始。');
        sessions.value = {};
        activeSessionIds.value = { gi: null, hsr: null };
        activeInstructionId.value = 'chat';  // 设置默认指令
      } else {
        // 兼容新旧格式的数据
        let cachedSessions, cachedActiveIds, cachedInstructionId;

        if (cachedState.version && cachedState.data) {
          // 新格式：有版本号和data包装
          ({ sessions: cachedSessions, activeSessionIds: cachedActiveIds, activeInstructionId: cachedInstructionId } = cachedState.data);
        } else {
          // 旧格式：直接数据
          cachedSessions = cachedState.sessions || cachedState;
          cachedActiveIds = cachedState.activeSessionIds || {};
          cachedInstructionId = cachedState.activeInstructionId || 'chat';
        }

        sessions.value = (typeof cachedSessions === 'object' && cachedSessions !== null) ? cachedSessions : {};

        // 清洗历史缓存中的消息结构，并修复过去记录中的 tool_result 消息状态
        Object.keys(sessions.value).forEach(sessionId => {
          const session = sessions.value[sessionId];
          if (session && typeof session === 'object') {
            ensureSessionMessageIntegrity(session);
            session.messageIds.forEach(messageId => {
              const message = session.messagesById[messageId];
              if (message) {
                // 确保所有 tool_result 消息状态为 'done'
                if (message.type === 'tool_result' && message.status !== 'done') {
                  message.status = 'done';
                }
                // 确保所有 tool_status 消息如果没有状态，设置为 'done'
                if (message.type === 'tool_status' && !message.status) {
                  message.status = 'done';
                }
              }
            });
          }
        });

        logger.log(`[AgentStore] 已恢复 ${Object.keys(sessions.value).length} 个会话，并修复了消息状态。`);

        const defaultIds = { gi: null, hsr: null };
        activeSessionIds.value = (typeof cachedActiveIds === 'object' && cachedActiveIds !== null)
                                 ? { ...defaultIds, ...cachedActiveIds }
                                 : defaultIds;
        logger.log('[AgentStore] 已恢复活动会话 ID。');

        // 恢复指令ID
        activeInstructionId.value = cachedInstructionId || 'chat';
        logger.log('[AgentStore] 已恢复活动指令 ID。');
      }

    } catch (e) {
      logger.error('[AgentStore] 缓存初始化期间发生严重错误，但不清除数据。请检查缓存格式。', e);
      // 尝试读取任何可用的数据，不再清除缓存
      try {
        const fallbackState = await sessionsStore.getItem<any>('state');
        if (fallbackState) {
          // 简单地尝试解析数据，不做版本检查
          const fallbackSessions = fallbackState.sessions || fallbackState.data?.sessions || {};
          const fallbackActiveIds = fallbackState.activeSessionIds || fallbackState.data?.activeSessionIds || { gi: null, hsr: null };
          const fallbackInstructionId = fallbackState.activeInstructionId || fallbackState.data?.activeInstructionId || 'chat';
          sessions.value = fallbackSessions;
          activeSessionIds.value = fallbackActiveIds;
          activeInstructionId.value = fallbackInstructionId;
          logger.log('[AgentStore] 成功从损坏的缓存中恢复了部分数据。');
        } else {
          sessions.value = {};
          activeSessionIds.value = { gi: null, hsr: null };
          activeInstructionId.value = 'chat';
        }
      } catch (fallbackError) {
        logger.error('[AgentStore] 备用恢复也失败了，使用空状态。', fallbackError);
        sessions.value = {};
        activeSessionIds.value = { gi: null, hsr: null };
        activeInstructionId.value = 'chat';
      }
    }
  }

  persistState(sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>, activeInstructionId: Ref<string>): () => void {
    const persistFn = debounce(async () => {
      try {
        const stateToPersist = {
          version: AGENT_CACHE_VERSION,
          data: {
            sessions: JSON.parse(JSON.stringify(sessions.value)),
            activeSessionIds: JSON.parse(JSON.stringify(activeSessionIds.value)),
            activeInstructionId: activeInstructionId.value,
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
