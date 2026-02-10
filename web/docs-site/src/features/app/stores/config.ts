import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';
import { nanoid } from 'nanoid';
import logger from '@/features/app/services/loggerService';
import type { Ref } from 'vue';
import type { AgentProtocolMode } from '@/features/agent/types';

// --- 类型定义 ---
export interface CustomParam {
    key: string;
    value: string;
}

export interface Config {
    id: string;
    name: string;
    provider: 'openai' | 'google' | 'deepseek' | 'iflow' | 'zhipu' | 'modelscope'; // 添加新提供商
    apiUrl: string;
    apiKey: string;
    modelName: string;
    temperature: number;
    stream: boolean;
    maxContextLength: number;
    requestInterval: number;
    maxIterations: number; // AI 迭代次数限制，0 表示无限制
    agentProtocolMode?: AgentProtocolMode;
    enableStructuredTools?: boolean;
    structuredToolsStrict?: boolean;
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
    provider: 'openai', // 默认为 openai
    apiUrl: oldApiUrl || '',
    apiKey: oldApiKey || '',
    modelName: modelName,
    temperature: parseFloat(localStorage.getItem('temperature') || '0.7'),
    stream: true,
    maxContextLength: parseInt(localStorage.getItem('maxContextLength') || '128000', 10),
    requestInterval: parseInt(localStorage.getItem('requestInterval') || '1000', 10),
    maxIterations: 10, // 默认迭代次数限制为 10
    agentProtocolMode: 'auto',
    enableStructuredTools: true,
    structuredToolsStrict: false,
    availableModels: [],
    modelsLastFetched: null,
    customParams: [], // 迁移时也初始化空数组
  };

  localStorage.removeItem('apiUrl');
  localStorage.removeItem('apiKey');
  localStorage.removeItem('modelName');
  localStorage.removeItem('temperature');
  localStorage.removeItem('maxContextLength');
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
        provider: c.provider || 'openai', // 向后兼容：旧数据默认为 openai
        customParams: c.customParams || [], // 确保向后兼容性
        availableModels: c.availableModels || [],
        modelsLastFetched: c.modelsLastFetched || null,
        maxIterations: c.maxIterations ?? 10, // 向后兼容：旧数据默认为 10
        agentProtocolMode: c.agentProtocolMode || 'auto',
        enableStructuredTools: c.enableStructuredTools ?? true,
        structuredToolsStrict: c.structuredToolsStrict ?? false,
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

    const initialModelName = configData.modelName || 'gpt-4-turbo';
    const newConfig: Config = {
      id: nanoid(),
      provider: 'openai',
      apiUrl: '',
      apiKey: '',
      modelName: initialModelName,
      temperature: 0.7,
      stream: true,
      maxContextLength: 65536,
      requestInterval: 1000,
      maxIterations: 10, // 默认迭代次数限制为 10
      agentProtocolMode: 'auto',
      enableStructuredTools: true,
      structuredToolsStrict: false,
      availableModels: [initialModelName], // 初始化时，第1项就是当前模型
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

      // 只要更新配置就重置缓存时间戳，强制刷新模型列表
      newValues.modelsLastFetched = null;
      logger.log(`配置已更新，重置模型列表缓存时间戳`);

      if (updates.availableModels) {
        newValues.modelsLastFetched = Date.now();
      }
      configs.value[configIndex] = { ...configs.value[configIndex], ...newValues };
      logger.log(`--- STORE ACTION: updateConfig 完成，ID: ${id} ---`);
    } else {
      logger.log(`--- STORE ACTION: updateConfig 失败。未找到 ID: ${id} ---`);
    }
  }

  function setCustomModel(id: string, modelName: string): void {
    const configIndex = configs.value.findIndex(c => c.id === id);
    if (configIndex !== -1) {
      const currentModels = [...(configs.value[configIndex].availableModels || [])];
      if (currentModels.length === 0) {
        currentModels.push(modelName);
      } else {
        currentModels[0] = modelName;
      }
      configs.value[configIndex].availableModels = currentModels;

      // 同时将当前使用的模型更新为这个自定义模型
      configs.value[configIndex].modelName = modelName;

      logger.log(`--- STORE ACTION: setCustomModel 完成。AvailableModels[0] 更新为 "${modelName}" ---`);
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

      const fetchedModelIds = models.map((model: any) => model.id).sort();

      // 逻辑核心：保留A表第1项，替换剩余部分为B表
      const currentModels = currentConfig.availableModels || [];
      const firstItem = currentModels.length > 0 ? currentModels[0] : currentConfig.modelName;

      // 构造新列表：[第1项, ...API列表]
      // 这里简单过滤掉重复项，以免列表中出现两个一模一样的 'gpt-4'
      const uniqueFetched = fetchedModelIds.filter((id: string) => id !== firstItem);
      const newAvailableModels = [firstItem, ...uniqueFetched];

      // 更新 Store
      const configIndex = configs.value.findIndex(c => c.id === currentConfig.id);
      if (configIndex !== -1) {
         configs.value[configIndex].availableModels = newAvailableModels;
         configs.value[configIndex].modelsLastFetched = Date.now();

         // 如果当前选中的模型不在新列表里（理论上不可能，因为第1项就是它），
         // 这里不需要额外的自动切换逻辑，因为我们保留了第1项。
      }

      logger.log("成功获取并更新了模型列表。", { count: newAvailableModels.length });

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
    setCustomModel,
  };
});
