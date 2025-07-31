import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';
import { nanoid } from 'nanoid';
import logger from '@/services/loggerService';

// --- 新的数据结构和持久化键 ---
const CONFIG_STORAGE_KEY = 'ai_configs_v2';

// --- 迁移逻辑：从旧的 localStorage 格式迁移数据 ---
function migrateFromOldStorage() {
  const oldApiUrl = localStorage.getItem('apiUrl');
  const oldApiKey = localStorage.getItem('apiKey');

  // 如果没有旧数据，则无需迁移
  if (!oldApiUrl && !oldApiKey) {
    return null;
  }

  logger.log("检测到旧版配置，正在执行一次性迁移...");

  const modelName = localStorage.getItem('modelName') || 'gpt-4';
  const defaultConfig = {
    id: nanoid(),
    name: `默认配置 (${modelName})`,
    apiUrl: oldApiUrl || '',
    apiKey: oldApiKey || '',
    modelName: modelName,
    temperature: parseFloat(localStorage.getItem('temperature')) || 0.7,
    stream: true,
    maxTokens: parseInt(localStorage.getItem('maxTokens')) || 128000,
    requestInterval: parseInt(localStorage.getItem('requestInterval')) || 1000,
    availableModels: [] // 初始化为空数组
  };

  // 清理旧的 localStorage 项
  localStorage.removeItem('apiUrl');
  localStorage.removeItem('apiKey');
  localStorage.removeItem('modelName');
  localStorage.removeItem('temperature');
  localStorage.removeItem('maxTokens');
  localStorage.removeItem('requestInterval');

  logger.log("旧版配置已成功迁移并清理。");

  return [defaultConfig];
}


// --- 从 localStorage 加载配置 ---
function loadConfigs() {
  const storedConfigs = localStorage.getItem(CONFIG_STORAGE_KEY);
  if (storedConfigs) {
    try {
      const loaded = JSON.parse(storedConfigs);
      // 确保存储的每个配置都符合当前的数据结构，特别是对于后面新增的字段
      return loaded.map(c => ({
        ...c,
        availableModels: c.availableModels || [],
        modelsLastFetched: c.modelsLastFetched || null,
      }));
    } catch (e) {
      logger.error("!!! CRITICAL: Failed to parse configs from localStorage. Data might be corrupt.", e);
      logger.error("!!! Corrupted Data:", storedConfigs);
      const migrated = migrateFromOldStorage();
      if (migrated) {
         logger.warn("!!! Fallback: Migrating from old data format as recovery.");
         return migrated;
      }
      return [];
    }
  }

  const migratedConfigs = migrateFromOldStorage();
  if (migratedConfigs) {
    return migratedConfigs;
  }

  return []; // 默认返回空数组
}


export const useConfigStore = defineStore('config', () => {
  // --- State ---
  const configs = ref(loadConfigs());
  const activeConfigId = ref(localStorage.getItem('activeConfigId') || (configs.value.length > 0 ? configs.value[0].id : null));
  const isFetchingModels = ref(false);

  // --- Computed Properties ---
  const activeConfig = computed(() => {
    // 如果没有激活的ID，或者configs为空，返回一个安全的默认结构
    if (!activeConfigId.value || configs.value.length === 0) {
      return null;
    }
    const config = configs.value.find(c => c.id === activeConfigId.value);
    // 如果找不到匹配的config（例如，它被删除了），则返回null
    return config || null;
  });

  // --- Watchers for localStorage persistence ---
  watch(configs, (newConfigs) => {
    try {
      // 根据用户要求，我们将包括 availableModels 在内的完整配置存入 localStorage。
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(newConfigs));
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        logger.error('!!! CRITICAL: localStorage quota exceeded. Could not save configs.');
        alert('错误：浏览器存储空间已满，无法保存新的AI配置。请清理浏览器缓存或删除一些不用的配置。');
      } else {
        logger.error('Failed to save configs to localStorage:', e);
      }
    }
  }, { deep: true });

  watch(activeConfigId, (newId) => {
    logger.log(`--- STORE: watch triggered for activeConfigId. New ID: ${newId} ---`);
    if (newId) {
      localStorage.setItem('activeConfigId', newId);
    } else {
      localStorage.removeItem('activeConfigId');
    }
    logger.log(`--- STORE: activeConfigId saved to localStorage ---`);
  });


  // --- Actions ---

  function addConfig(configData = {}) {
    logger.log('--- STORE ACTION: addConfig started ---', configData);
    if (configs.value.length >= 13) {
      logger.log("配置数量已达上限 (13)，无法添加新配置。");
      return null;
    }

    // 智能默认命名：如果未提供名称，则生成一个唯一的“未命名”名称
    let newName = configData.name;
    if (!newName) {
      const unnamedCount = configs.value.filter(c => c.name.startsWith('未命名')).length;
      newName = unnamedCount > 0 ? `未命名 ${unnamedCount + 1}` : '未命名';
    }

    const newConfig = {
      id: nanoid(),
      name: newName,
      apiUrl: '',
      apiKey: '',
      modelName: 'gpt-4-turbo', // 保留一个默认的技术模型名
      temperature: 0.7,
      stream: true,
      maxTokens: 65536, // 修正：默认上下文限制为 64K
      requestInterval: 1000,
      availableModels: [],
      modelsLastFetched: null, // 初始化缓存时间戳
      ...configData, // 传入的数据可以覆盖以上任何默认值
      name: newName, // 确保最终名称是我们计算出的新名称
    };
    configs.value.push(newConfig);
    activeConfigId.value = newConfig.id;
    logger.log(`--- STORE ACTION: addConfig finished. New config pushed, and activeConfigId set to ${newConfig.id} ---`);
    return newConfig;
  }

  function updateConfig(id, updates) {
    logger.log(`--- STORE ACTION: updateConfig started for id: ${id} ---`, updates);
    const configIndex = configs.value.findIndex(c => c.id === id);
    if (configIndex !== -1) {
      const newValues = { ...updates };
      // 如果正在更新模型列表，则自动更新时间戳
      if (updates.availableModels) {
        newValues.modelsLastFetched = Date.now();
      }
      configs.value[configIndex] = { ...configs.value[configIndex], ...newValues };
      logger.log(`--- STORE ACTION: updateConfig finished for id: ${id} ---`);
    } else {
      logger.log(`--- STORE ACTION: updateConfig failed. ID not found: ${id} ---`);
    }
  }

  function deleteConfig(id) {
    logger.log(`--- STORE ACTION: deleteConfig started for id: ${id} ---`);
    const indexToDelete = configs.value.findIndex(c => c.id === id);
    if (indexToDelete === -1) {
      logger.log(`--- STORE ACTION: deleteConfig failed. ID not found: ${id} ---`);
      return;
    }

    const wasActive = activeConfigId.value === id;
    logger.log(`--- STORE ACTION: Item to delete found at index ${indexToDelete}. Was active? ${wasActive} ---`);

    configs.value.splice(indexToDelete, 1);
    logger.log(`--- STORE ACTION: Item ${id} removed from configs array. ---`);

    if (wasActive) {
      if (configs.value.length === 0) {
        activeConfigId.value = null;
        logger.log('--- STORE ACTION: List is now empty, activeConfigId set to null. ---');
      } else {
        const newActiveIndex = Math.max(0, indexToDelete - 1);
        activeConfigId.value = configs.value[newActiveIndex].id;
        logger.log(`--- STORE ACTION: Deleted item was active. New active index is ${newActiveIndex}, new active ID is ${activeConfigId.value}. ---`);
      }
    }
  }

  function setActiveConfig(id) {
    logger.log(`--- STORE ACTION: setActiveConfig started for id: ${id} ---`);
    if (configs.value.some(c => c.id === id)) {
      activeConfigId.value = id;
      logger.log(`--- STORE ACTION: setActiveConfig finished. activeConfigId is now ${id}. ---`);
    } else {
      logger.error(`--- STORE ACTION: setActiveConfig failed. Attempted to activate a non-existent config ID: ${id} ---`);
    }
  }

  async function fetchModels() {
    const currentConfig = activeConfig.value;
    if (!currentConfig || !currentConfig.apiUrl || !currentConfig.apiKey) {
      logger.error("无法获取模型列表：当前激活的配置无效或不完整。");
      if (currentConfig) {
        updateConfig(currentConfig.id, { availableModels: [] });
      }
      return;
    }

    // --- 缓存检查逻辑 ---
    const CACHE_DURATION = 10 * 60 * 1000; // 10 分钟
    const now = Date.now();
    const lastFetched = currentConfig.modelsLastFetched;

    if (lastFetched && (now - lastFetched < CACHE_DURATION) && currentConfig.availableModels && currentConfig.availableModels.length > 0) {
      logger.log("模型列表缓存有效，跳过网络请求。");
      return;
    }

    isFetchingModels.value = true;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      logger.error("获取模型列表超时 (10秒)。");
    }, 10000); // 10-second timeout

    const baseUrl = currentConfig.apiUrl.replace(/\/$/, '');
    const modelsUrl = `${baseUrl}/models`;

    try {
      logger.log("正在从 API 获取模型列表...", { url: modelsUrl });
      const response = await fetch(modelsUrl, {
        headers: { 'Authorization': `Bearer ${currentConfig.apiKey}` },
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`API 请求失败: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const models = Array.isArray(data) ? data : (data.data || []);
      
      const modelIds = models.map(model => model.id).sort();
      
      // 注意：updateConfig 现在会自动处理时间戳
      updateConfig(currentConfig.id, { availableModels: modelIds });
      
      logger.log("成功获取并更新了模型列表。", { count: modelIds.length });

      // 检查当前选定的模型是否在新的列表中
      // 这里需要从configs.value中获取最新的config，因为updateConfig是异步的
      const updatedConfig = configs.value.find(c => c.id === currentConfig.id);
      if (modelIds.length > 0 && !modelIds.includes(updatedConfig.modelName)) {
        updateConfig(currentConfig.id, { modelName: modelIds[0] });
        logger.log("当前选中模型无效，已自动切换为:", modelIds[0]);
      }

    } catch (error) {
       logger.error("获取模型列表失败:", error.name === 'AbortError' ? '请求超时' : error);
       if (activeConfig.value) {
         // 失败时清除缓存，以触发下次刷新
        updateConfig(activeConfig.value.id, { availableModels: [], modelsLastFetched: null });
       }
    } finally {
      clearTimeout(timeoutId);
      isFetchingModels.value = false;
    }
  }

  return {
    configs,
    activeConfigId,
    activeConfig,
    isFetchingModels,
    // Actions
    addConfig,
    updateConfig,
    deleteConfig,
    setActiveConfig,
    fetchModels,
  };
});