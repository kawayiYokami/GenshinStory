import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';
import { nanoid } from 'nanoid';
import logger from '@/features/app/services/loggerService';
import type { Ref } from 'vue';

// --- 类型定义 ---
export interface CustomParam {
    key: string;
    value: string;
}

export interface Config {
    id: string;
    name: string;
    apiUrl: string;
    apiKey: string;
    modelName: string;
    temperature: number;
    stream: boolean;
    maxTokens: number;
    requestInterval: number;
    availableModels: string[];
    modelsLastFetched: number | null;
    customParams?: CustomParam[];
}

const CONFIG_STORAGE_KEY = 'ai_configs_v2';

// --- 迁移逻辑 ---
function migrateFromOldStorage(): Config[] | null {
  const oldApiUrl = localStorage.getItem('apiUrl');
  const oldApiKey = localStorage.getItem('apiKey');

  if (!oldApiUrl && !oldApiKey) {
    return null;
  }

  logger.log("检测到旧版配置，正在执行一次性迁移...");

  const modelName = localStorage.getItem('modelName') || 'gpt-4';
  const defaultConfig: Config = {
    id: nanoid(),
    name: `默认配置 (${modelName})`,
    apiUrl: oldApiUrl || '',
    apiKey: oldApiKey || '',
    modelName: modelName,
    temperature: parseFloat(localStorage.getItem('temperature') || '0.7'),
    stream: true,
    maxTokens: parseInt(localStorage.getItem('maxTokens') || '128000', 10),
    requestInterval: parseInt(localStorage.getItem('requestInterval') || '1000', 10),
    availableModels: [],
    modelsLastFetched: null,
    customParams: [], // 迁移时也初始化空数组
  };

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
function loadConfigs(): Config[] {
  const storedConfigs = localStorage.getItem(CONFIG_STORAGE_KEY);
  if (storedConfigs) {
    try {
      const loaded = JSON.parse(storedConfigs) as Config[];
      return loaded.map(c => ({
        ...c,
        customParams: c.customParams || [], // 确保向后兼容性
        availableModels: c.availableModels || [],
        modelsLastFetched: c.modelsLastFetched || null,
      }));
    } catch (e) {
      logger.error("!!! 严重: 从 localStorage 解析配置失败。数据可能已损坏。", e);
      logger.error("!!! 损坏的数据:", storedConfigs);
      const migrated = migrateFromOldStorage();
      if (migrated) {
         logger.warn("!!! 回退: 作为恢复手段，从旧数据格式迁移。");
         return migrated;
      }
      return [];
    }
  }

  const migratedConfigs = migrateFromOldStorage();
  if (migratedConfigs) {
    return migratedConfigs;
  }

  return [];
}

export const useConfigStore = defineStore('config', () => {
  // --- 状态 ---
  const configs: Ref<Config[]> = ref(loadConfigs());
  const activeConfigId: Ref<string | null> = ref(localStorage.getItem('activeConfigId') || (configs.value.length > 0 ? configs.value[0].id : null));
  const isFetchingModels = ref(false);

  // --- 计算属性 ---
  const activeConfig = computed(() => {
    if (!activeConfigId.value || configs.value.length === 0) {
      return null;
    }
    const config = configs.value.find(c => c.id === activeConfigId.value);
    return config || null;
  });

  // --- 监听器 ---
  watch(configs, (newConfigs) => {
    try {
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(newConfigs));
    } catch (e: any) {
      if (e.name === 'QuotaExceededError') {
        logger.error('!!! 严重: localStorage 配额超出。无法保存配置。');
        alert('错误：浏览器存储空间已满，无法保存新的AI配置。请清理浏览器缓存或删除一些不用的配置。');
      } else {
        logger.error('保存配置到 localStorage 失败:', e);
      }
    }
  }, { deep: true });

  watch(activeConfigId, (newId) => {
    logger.log(`--- STORE: activeConfigId 的 watch 已触发。新 ID: ${newId} ---`);
    if (newId) {
      localStorage.setItem('activeConfigId', newId);
    } else {
      localStorage.removeItem('activeConfigId');
    }
    logger.log(`--- STORE: activeConfigId 已保存到 localStorage ---`);
  });

  // --- Actions ---
  function addConfig(configData: Partial<Config> = {}): Config | null {
    logger.log('--- STORE ACTION: addConfig 开始 ---', configData);
    if (configs.value.length >= 13) {
      logger.log("配置数量已达上限 (13)，无法添加新配置。");
      return null;
    }

    let newName = configData.name;
    if (!newName) {
      const unnamedCount = configs.value.filter(c => c.name.startsWith('未命名')).length;
      newName = unnamedCount > 0 ? `未命名 ${unnamedCount + 1}` : '未命名';
    }

    const newConfig: Config = {
      id: nanoid(),
      apiUrl: '',
      apiKey: '',
      modelName: 'gpt-4-turbo',
      temperature: 0.7,
      stream: true,
      maxTokens: 65536,
      requestInterval: 1000,
      availableModels: [],
      modelsLastFetched: null,
      customParams: [], // 新配置初始化空的自定义参数数组
      ...configData,
      name: newName,
    };
    configs.value.push(newConfig);
    activeConfigId.value = newConfig.id;
    logger.log(`--- STORE ACTION: addConfig 完成。新配置已推送，activeConfigId 设置为 ${newConfig.id} ---`);
    return newConfig;
  }

  function updateConfig(id: string, updates: Partial<Config>): void {
    logger.log(`--- STORE ACTION: updateConfig 开始，ID: ${id} ---`, updates);
    const configIndex = configs.value.findIndex(c => c.id === id);
    if (configIndex !== -1) {
      const newValues = { ...updates };
      if (updates.availableModels) {
        newValues.modelsLastFetched = Date.now();
      }
      configs.value[configIndex] = { ...configs.value[configIndex], ...newValues };
      logger.log(`--- STORE ACTION: updateConfig 完成，ID: ${id} ---`);
    } else {
      logger.log(`--- STORE ACTION: updateConfig 失败。未找到 ID: ${id} ---`);
    }
  }

  function deleteConfig(id: string): void {
    logger.log(`--- STORE ACTION: deleteConfig 开始，ID: ${id} ---`);
    const indexToDelete = configs.value.findIndex(c => c.id === id);
    if (indexToDelete === -1) {
      logger.log(`--- STORE ACTION: deleteConfig 失败。未找到 ID: ${id} ---`);
      return;
    }

    const wasActive = activeConfigId.value === id;
    logger.log(`--- STORE ACTION: 在索引 ${indexToDelete} 找到要删除的项目。是否为活动项? ${wasActive} ---`);

    configs.value.splice(indexToDelete, 1);
    logger.log(`--- STORE ACTION: 项目 ${id} 已从配置数组中移除。 ---`);

    if (wasActive) {
      if (configs.value.length === 0) {
        activeConfigId.value = null;
        logger.log('--- STORE ACTION: 列表现为空，activeConfigId 已设为 null。 ---');
      } else {
        const newActiveIndex = Math.max(0, indexToDelete - 1);
        activeConfigId.value = configs.value[newActiveIndex].id;
        logger.log(`--- STORE ACTION: 删除的项目是活动项。新活动索引为 ${newActiveIndex}，新活动 ID 为 ${activeConfigId.value}。 ---`);
      }
    }
  }

  function setActiveConfig(id: string): void {
    logger.log(`--- STORE ACTION: setActiveConfig 开始，ID: ${id} ---`);
    if (configs.value.some(c => c.id === id)) {
      activeConfigId.value = id;
      logger.log(`--- STORE ACTION: setActiveConfig 完成。activeConfigId 现在是 ${id}。 ---`);
    } else {
      logger.error(`--- STORE ACTION: setActiveConfig 失败。尝试激活一个不存在的配置 ID: ${id} ---`);
    }
  }

  async function fetchModels(): Promise<void> {
    const currentConfig = activeConfig.value;
    if (!currentConfig || !currentConfig.apiUrl || !currentConfig.apiKey) {
      logger.error("无法获取模型列表：当前激活的配置无效或不完整。");
      if (currentConfig) {
        updateConfig(currentConfig.id, { availableModels: [] });
      }
      return;
    }

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
    }, 10000);

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
      
      const modelIds = models.map((model: any) => model.id).sort();
      
      updateConfig(currentConfig.id, { availableModels: modelIds });
      
      logger.log("成功获取并更新了模型列表。", { count: modelIds.length });

      const updatedConfig = configs.value.find(c => c.id === currentConfig.id);
      if (updatedConfig && modelIds.length > 0 && !modelIds.includes(updatedConfig.modelName)) {
        updateConfig(currentConfig.id, { modelName: modelIds[0] });
        logger.log("当前选中模型无效，已自动切换为:", modelIds[0]);
      }

    } catch (error: any) {
       logger.error("获取模型列表失败:", error.name === 'AbortError' ? '请求超时' : error);
       if (activeConfig.value) {
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
    addConfig,
    updateConfig,
    deleteConfig,
    setActiveConfig,
    fetchModels,
  };
});