import logger from '@/features/app/services/loggerService';
import { sessionsStore, lastUsedRolesStore } from '@/features/app/services/storageFacade';

class AgentCacheService {
  public async forceClearAgentCache(): Promise<void> {
    await sessionsStore.clear();
    await lastUsedRolesStore.clear();
    logger.warn('[AgentCacheService] 缓存因数据过时或损坏已被清除。');
  }
}

export const agentCacheService = new AgentCacheService();
