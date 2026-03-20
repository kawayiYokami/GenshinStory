import localforage from 'localforage';

export const STORAGE_KEYS = {
  appTheme: 'app-theme',
  currentDomain: 'currentDomain',
  configList: 'ai_configs_v2',
  activeConfigId: 'activeConfigId',
  customInstructions: 'customInstructions',
  customPersonas: 'customPersonas',
  dataVersion: 'dataVersion',
  legacyApiUrl: 'apiUrl',
  legacyApiKey: 'apiKey',
  legacyModelName: 'modelName',
  legacyTemperature: 'temperature',
  legacyMaxContextLength: 'maxContextLength',
  legacyRequestInterval: 'requestInterval',
} as const;

export const LOCALFORAGE_STORES = {
  catalogTreeCache: 'catalogTreeCache',
  agentSessions: 'agentSessions',
  lastUsedRoles: 'lastUsedRoles',
  memoryLibrary: 'memoryLibrary',
} as const;

type LocalStorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS];

interface KeyValueStore {
  keys(): Promise<string[]>;
  getItem<T = unknown>(key: string): Promise<T | null>;
  setItem<T = unknown>(key: string, value: T): Promise<T>;
  clear(): Promise<void>;
}

function safeJsonParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

class StorageFacade {
  public readonly stores = {
    catalogTreeStore: localforage.createInstance({ name: LOCALFORAGE_STORES.catalogTreeCache }),
    sessionsStore: localforage.createInstance({ name: LOCALFORAGE_STORES.agentSessions }),
    lastUsedRolesStore: localforage.createInstance({ name: LOCALFORAGE_STORES.lastUsedRoles }),
    memoryLibraryStore: localforage.createInstance({ name: LOCALFORAGE_STORES.memoryLibrary }),
  };

  public getString(key: LocalStorageKey): string | null {
    return localStorage.getItem(key);
  }

  public setString(key: LocalStorageKey, value: string): void {
    localStorage.setItem(key, value);
  }

  public remove(key: LocalStorageKey): void {
    localStorage.removeItem(key);
  }

  public getJson<T>(key: LocalStorageKey, fallback: T): T {
    return safeJsonParse<T>(this.getString(key), fallback);
  }

  public setJson(key: LocalStorageKey, value: unknown): void {
    this.setString(key, JSON.stringify(value));
  }

  public getConfigList<T = unknown[]>(): T {
    return this.getJson<T>(STORAGE_KEYS.configList, [] as unknown as T);
  }

  public setConfigList(value: unknown): void {
    this.setJson(STORAGE_KEYS.configList, value);
  }

  public getActiveConfigId(): string | null {
    return this.getString(STORAGE_KEYS.activeConfigId);
  }

  public setActiveConfigId(id: string | null): void {
    if (id) {
      this.setString(STORAGE_KEYS.activeConfigId, id);
      return;
    }
    this.remove(STORAGE_KEYS.activeConfigId);
  }

  public getCurrentDomain(): string | null {
    return this.getString(STORAGE_KEYS.currentDomain);
  }

  public setCurrentDomain(domain: string | null): void {
    if (domain) {
      this.setString(STORAGE_KEYS.currentDomain, domain);
      return;
    }
    this.remove(STORAGE_KEYS.currentDomain);
  }

  public getTheme(): string | null {
    return this.getString(STORAGE_KEYS.appTheme);
  }

  public setTheme(theme: string): void {
    this.setString(STORAGE_KEYS.appTheme, theme);
  }

  public getCustomInstructions<T = unknown[]>(): T {
    return this.getJson<T>(STORAGE_KEYS.customInstructions, [] as unknown as T);
  }

  public setCustomInstructions(value: unknown): void {
    this.setJson(STORAGE_KEYS.customInstructions, value);
  }

  public getCustomPersonas<T = unknown[]>(): T {
    return this.getJson<T>(STORAGE_KEYS.customPersonas, [] as unknown as T);
  }

  public setCustomPersonas(value: unknown): void {
    this.setJson(STORAGE_KEYS.customPersonas, value);
  }

  public getDataVersion(): string | null {
    return this.getString(STORAGE_KEYS.dataVersion);
  }

  public setDataVersion(version: string | null): void {
    if (version) {
      this.setString(STORAGE_KEYS.dataVersion, version);
      return;
    }
    this.remove(STORAGE_KEYS.dataVersion);
  }

  public getLegacyConfigSnapshot(): Record<string, string | null> {
    return {
      apiUrl: this.getString(STORAGE_KEYS.legacyApiUrl),
      apiKey: this.getString(STORAGE_KEYS.legacyApiKey),
      modelName: this.getString(STORAGE_KEYS.legacyModelName),
      temperature: this.getString(STORAGE_KEYS.legacyTemperature),
      maxContextLength: this.getString(STORAGE_KEYS.legacyMaxContextLength),
      requestInterval: this.getString(STORAGE_KEYS.legacyRequestInterval),
    };
  }

  public clearLegacyConfigSnapshot(): void {
    this.remove(STORAGE_KEYS.legacyApiUrl);
    this.remove(STORAGE_KEYS.legacyApiKey);
    this.remove(STORAGE_KEYS.legacyModelName);
    this.remove(STORAGE_KEYS.legacyTemperature);
    this.remove(STORAGE_KEYS.legacyMaxContextLength);
    this.remove(STORAGE_KEYS.legacyRequestInterval);
  }

  public async readAllStoreEntries(store: KeyValueStore): Promise<Record<string, unknown>> {
    const entries: Record<string, unknown> = {};
    const keys = await store.keys();
    for (const key of keys) {
      entries[key] = await store.getItem(key);
    }
    return entries;
  }

  public async replaceStoreEntries(store: KeyValueStore, entries: Record<string, unknown>): Promise<void> {
    await store.clear();
    const keys = Object.keys(entries);
    for (const key of keys) {
      await store.setItem(key, entries[key]);
    }
  }
}

export const storageFacade = new StorageFacade();

export const catalogTreeStore = storageFacade.stores.catalogTreeStore;
export const sessionsStore = storageFacade.stores.sessionsStore;
export const lastUsedRolesStore = storageFacade.stores.lastUsedRolesStore;
export const memoryLibraryStore = storageFacade.stores.memoryLibraryStore;

export default storageFacade;
