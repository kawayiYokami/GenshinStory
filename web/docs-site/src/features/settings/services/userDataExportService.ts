import storageFacade, {
  STORAGE_KEYS,
  sessionsStore,
  lastUsedRolesStore,
} from '@/features/app/services/storageFacade';
import memoryStoreService, { type MemoryRecord } from '@/features/memory/services/memoryStoreService';

const AGENT_CACHE_VERSION = '2.0';

interface PersistedStores {
  agentSessions: Record<string, unknown>;
  lastUsedRoles: Record<string, unknown>;
}

interface LiveSnapshot {
  sessions: unknown;
  activeSessionIds: unknown;
  activeInstructionId: string | null;
}

export interface UserDataExportOverrides {
  settings?: {
    currentDomain?: string | null;
    currentTheme?: string | null;
    configs?: unknown;
    activeConfigId?: string | null;
  };
  chat?: {
    sessions?: unknown;
    activeSessionIds?: unknown;
    activeInstructionId?: string | null;
  };
}

export interface UserDataExportPayload {
  schemaVersion: string;
  exportedAt: string;
  settings: {
    domain: string | null;
    theme: string | null;
    dataVersion: string | null;
    aiConfig: {
      activeConfigId: string | null;
      configs: unknown;
    };
    customPrompts: {
      instructions: unknown[];
      personas: unknown[];
    };
  };
  chat: {
    persistedStores: PersistedStores;
    liveSnapshot: LiveSnapshot;
  };
  memoryLibrary: {
    implemented: false;
    schemaVersion: string;
    records: MemoryRecord[];
    interfaces: {
      list: null;
      upsert: null;
      remove: null;
    };
    note: string;
  };
  debug: {
    localStorage: {
      keysSeen: string[];
      legacy: Record<string, string | null>;
    };
  };
}

export interface UserDataImportPayload {
  schemaVersion?: string;
  exportedAt?: string;
  settings?: Partial<UserDataExportPayload['settings']>;
  chat?: Partial<UserDataExportPayload['chat']>;
  memoryLibrary?: Partial<UserDataExportPayload['memoryLibrary']>;
}

export type UserDataImportStrategy = 'preview' | 'merge' | 'overwrite';

export interface UserDataExportResult {
  fileName: string;
  sizeBytes: number;
}

export interface UserDataImportSummary {
  schemaVersion: string;
  exportedAt: string | null;
  configs: number;
  customInstructions: number;
  customPersonas: number;
  persistedSessionKeys: number;
  sessionCount: number;
  lastUsedRoles: number;
  memoryRecords: number;
}

export interface UserDataImportResult {
  strategy: UserDataImportStrategy;
  applied: boolean;
  summary: UserDataImportSummary;
  warnings: string[];
}

export type MemoryLibraryExportPayload = MemoryRecord[];

export type MemoryLibraryImportPayload = MemoryRecord[];

export interface MemoryLibraryImportSummary {
  schemaVersion: string;
  exportedAt: string | null;
  memoryRecords: number;
}

export interface MemoryLibraryImportResult {
  strategy: UserDataImportStrategy;
  applied: boolean;
  summary: MemoryLibraryImportSummary;
  warnings: string[];
}

interface NormalizedAgentState {
  sessions: Record<string, unknown>;
  activeSessionIds: Record<string, string | null>;
  activeInstructionId: string;
}

function safeParseArray(raw: string | null): unknown[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function safeParseJson<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function cloneSerializable<T>(value: T): T {
  if (value === null || value === undefined) return value;
  try {
    if (typeof structuredClone === 'function') {
      return structuredClone(value);
    }
  } catch {
    // fallback below
  }
  try {
    return JSON.parse(JSON.stringify(value)) as T;
  } catch {
    return value;
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asStringOrNull(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

function normalizeImportPayload(raw: unknown): UserDataImportPayload {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return {};
  }

  const payload = raw as Record<string, unknown>;
  return {
    schemaVersion: typeof payload.schemaVersion === 'string' ? payload.schemaVersion : undefined,
    exportedAt: typeof payload.exportedAt === 'string' ? payload.exportedAt : undefined,
    settings: asRecord(payload.settings) as UserDataImportPayload['settings'],
    chat: asRecord(payload.chat) as UserDataImportPayload['chat'],
    memoryLibrary: asRecord(payload.memoryLibrary) as UserDataImportPayload['memoryLibrary'],
  };
}

function normalizeAgentState(raw: unknown): NormalizedAgentState {
  const defaultState: NormalizedAgentState = {
    sessions: {},
    activeSessionIds: { gi: null, hsr: null },
    activeInstructionId: 'chat',
  };

  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return defaultState;
  }

  const top = raw as Record<string, unknown>;
  const hasEnvelope = top.data && typeof top.data === 'object' && !Array.isArray(top.data);
  const source = hasEnvelope ? (top.data as Record<string, unknown>) : top;

  const sessions = asRecord(source.sessions || source);
  const activeSessionIds = asRecord(source.activeSessionIds);
  const activeInstructionId = asStringOrNull(source.activeInstructionId) || 'chat';

  return {
    sessions,
    activeSessionIds: {
      gi: asStringOrNull(activeSessionIds.gi),
      hsr: asStringOrNull(activeSessionIds.hsr),
      zzz: asStringOrNull(activeSessionIds.zzz),
    },
    activeInstructionId,
  };
}

function toAgentStateEnvelope(state: NormalizedAgentState): Record<string, unknown> {
  return {
    version: AGENT_CACHE_VERSION,
    data: {
      sessions: state.sessions,
      activeSessionIds: state.activeSessionIds,
      activeInstructionId: state.activeInstructionId,
    },
  };
}

function mergeByIdArray(localItems: unknown[], importedItems: unknown[]): unknown[] {
  const result = [...localItems];
  const idToIndex = new Map<string, number>();

  for (let index = 0; index < result.length; index += 1) {
    const item = result[index];
    const id = item && typeof item === 'object' ? (item as Record<string, unknown>).id : null;
    if (typeof id === 'string') {
      idToIndex.set(id, index);
    }
  }

  for (const incoming of importedItems) {
    const id = incoming && typeof incoming === 'object' ? (incoming as Record<string, unknown>).id : null;
    if (typeof id === 'string' && idToIndex.has(id)) {
      result[idToIndex.get(id)!] = incoming;
      continue;
    }
    if (typeof id === 'string') {
      idToIndex.set(id, result.length);
    }
    result.push(incoming);
  }

  return result;
}

function normalizeMemoryRecords(records: unknown[]): MemoryRecord[] {
  return records
    .map(item => asRecord(item))
    .filter(item => typeof item.id === 'string' && typeof item.content === 'string')
    .map(item => {
      const now = new Date().toISOString();
      const keywords = Array.isArray(item.keywords)
        ? item.keywords.filter(keyword => typeof keyword === 'string')
        : [];
      return {
        id: item.id as string,
        content: item.content as string,
        keywords,
        createdAt: typeof item.createdAt === 'string' ? item.createdAt : now,
        updatedAt: typeof item.updatedAt === 'string' ? item.updatedAt : now,
        metadata: item.metadata && typeof item.metadata === 'object'
          ? (item.metadata as Record<string, unknown>)
          : undefined,
      };
    });
}

function countSessionsFromPersistedEntries(entries: Record<string, unknown>): number {
  const state = normalizeAgentState(entries.state);
  return Object.keys(state.sessions).length;
}

function buildLiveSnapshotFromPayload(payload: UserDataImportPayload): NormalizedAgentState | null {
  const snapshot = asRecord(payload.chat?.liveSnapshot);
  if (!snapshot.sessions || typeof snapshot.sessions !== 'object') {
    return null;
  }

  return {
    sessions: asRecord(snapshot.sessions),
    activeSessionIds: {
      ...normalizeAgentState({ activeSessionIds: snapshot.activeSessionIds }).activeSessionIds,
    },
    activeInstructionId: asStringOrNull(snapshot.activeInstructionId) || 'chat',
  };
}

function analyzeImportPayload(payload: UserDataImportPayload): UserDataImportSummary {
  const importedConfigs = asArray(payload.settings?.aiConfig?.configs);
  const importedInstructions = asArray(payload.settings?.customPrompts?.instructions);
  const importedPersonas = asArray(payload.settings?.customPrompts?.personas);
  const importedSessionEntries = asRecord(payload.chat?.persistedStores?.agentSessions);
  const importedRoles = asRecord(payload.chat?.persistedStores?.lastUsedRoles);
  const importedMemory = asArray(payload.memoryLibrary?.records);

  let sessionCount = countSessionsFromPersistedEntries(importedSessionEntries);
  if (sessionCount === 0) {
    const liveState = buildLiveSnapshotFromPayload(payload);
    sessionCount = liveState ? Object.keys(liveState.sessions).length : 0;
  }

  return {
    schemaVersion: payload.schemaVersion || 'unknown',
    exportedAt: payload.exportedAt || null,
    configs: importedConfigs.length,
    customInstructions: importedInstructions.length,
    customPersonas: importedPersonas.length,
    persistedSessionKeys: Object.keys(importedSessionEntries).length,
    sessionCount,
    lastUsedRoles: Object.keys(importedRoles).length,
    memoryRecords: importedMemory.length,
  };
}

function buildMemoryImportSummary(payload: MemoryLibraryImportPayload): MemoryLibraryImportSummary {
  const importedRecords = normalizeMemoryRecords(payload as unknown[]);
  return {
    schemaVersion: 'json',
    exportedAt: null,
    memoryRecords: importedRecords.length,
  };
}

function formatDateForFileName(date: Date): string {
  return date.toISOString().replace(/[:.]/g, '-');
}

function downloadJson(payload: unknown, filePrefix: string): UserDataExportResult {
  const now = new Date();
  const fileName = `${filePrefix}-${formatDateForFileName(now)}.json`;
  const serialized = JSON.stringify(payload, null, 2);
  const blob = new Blob([serialized], { type: 'application/json;charset=utf-8' });
  const objectUrl = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = fileName;
  link.click();

  setTimeout(() => {
    URL.revokeObjectURL(objectUrl);
  }, 0);

  return {
    fileName,
    sizeBytes: blob.size,
  };
}

async function applySettingsImport(
  payload: UserDataImportPayload,
  strategy: UserDataImportStrategy
): Promise<void> {
  const settings = payload.settings || {};

  if ('domain' in settings) {
    storageFacade.setCurrentDomain(asStringOrNull(settings.domain));
  }

  if ('theme' in settings) {
    const importedTheme = asStringOrNull(settings.theme);
    if (importedTheme) {
      storageFacade.setTheme(importedTheme);
    }
  }

  if ('dataVersion' in settings) {
    storageFacade.setDataVersion(asStringOrNull(settings.dataVersion));
  }

  const importedConfigs = asArray(settings.aiConfig?.configs);
  if (importedConfigs.length > 0 || strategy === 'overwrite') {
    const localConfigs = storageFacade.getConfigList<unknown[]>();
    const nextConfigs = strategy === 'overwrite'
      ? importedConfigs
      : mergeByIdArray(localConfigs, importedConfigs);
    storageFacade.setConfigList(nextConfigs);
  }

  if ('activeConfigId' in (settings.aiConfig || {})) {
    storageFacade.setActiveConfigId(asStringOrNull(settings.aiConfig?.activeConfigId));
  }

  const importedInstructions = asArray(settings.customPrompts?.instructions);
  if (importedInstructions.length > 0 || strategy === 'overwrite') {
    const localInstructions = storageFacade.getCustomInstructions<unknown[]>();
    const nextInstructions = strategy === 'overwrite'
      ? importedInstructions
      : mergeByIdArray(localInstructions, importedInstructions);
    storageFacade.setCustomInstructions(nextInstructions);
  }

  const importedPersonas = asArray(settings.customPrompts?.personas);
  if (importedPersonas.length > 0 || strategy === 'overwrite') {
    const localPersonas = storageFacade.getCustomPersonas<unknown[]>();
    const nextPersonas = strategy === 'overwrite'
      ? importedPersonas
      : mergeByIdArray(localPersonas, importedPersonas);
    storageFacade.setCustomPersonas(nextPersonas);
  }
}

async function applyChatImport(
  payload: UserDataImportPayload,
  strategy: UserDataImportStrategy
): Promise<void> {
  const importedSessionEntries = cloneSerializable(asRecord(payload.chat?.persistedStores?.agentSessions));
  const importedRoles = cloneSerializable(asRecord(payload.chat?.persistedStores?.lastUsedRoles));
  const liveSnapshotState = buildLiveSnapshotFromPayload(payload);

  if (!('state' in importedSessionEntries) && liveSnapshotState) {
    importedSessionEntries.state = toAgentStateEnvelope(liveSnapshotState);
  }

  if (strategy === 'overwrite') {
    const normalizedImportedState = normalizeAgentState(importedSessionEntries.state);
    importedSessionEntries.state = toAgentStateEnvelope(normalizedImportedState);
    await storageFacade.replaceStoreEntries(sessionsStore, importedSessionEntries);
    await storageFacade.replaceStoreEntries(lastUsedRolesStore, importedRoles);
    return;
  }

  const localSessionEntries = await storageFacade.readAllStoreEntries(sessionsStore);
  const localRoles = await storageFacade.readAllStoreEntries(lastUsedRolesStore);

  const mergedSessionEntries = {
    ...localSessionEntries,
    ...importedSessionEntries,
  };

  const mergedState = {
    sessions: {
      ...normalizeAgentState(localSessionEntries.state).sessions,
      ...normalizeAgentState(importedSessionEntries.state).sessions,
    },
    activeSessionIds: {
      ...normalizeAgentState(localSessionEntries.state).activeSessionIds,
      ...normalizeAgentState(importedSessionEntries.state).activeSessionIds,
    },
    activeInstructionId:
      normalizeAgentState(importedSessionEntries.state).activeInstructionId
      || normalizeAgentState(localSessionEntries.state).activeInstructionId
      || 'chat',
  };

  mergedSessionEntries.state = toAgentStateEnvelope(mergedState);
  await storageFacade.replaceStoreEntries(sessionsStore, mergedSessionEntries);

  const mergedRoles = {
    ...localRoles,
    ...importedRoles,
  };
  await storageFacade.replaceStoreEntries(lastUsedRolesStore, mergedRoles);
}

async function applyMemoryImport(
  payload: UserDataImportPayload,
  strategy: UserDataImportStrategy
): Promise<void> {
  const importedRecords = normalizeMemoryRecords(asArray(payload.memoryLibrary?.records));
  if (strategy === 'overwrite') {
    await memoryStoreService.replaceAll(importedRecords);
    return;
  }

  await memoryStoreService.mergeAll(importedRecords);
}

async function applyMemoryImportRecords(
  records: unknown[],
  strategy: Exclude<UserDataImportStrategy, 'preview'>
): Promise<void> {
  const importedRecords = normalizeMemoryRecords(records);
  if (strategy === 'overwrite') {
    await memoryStoreService.replaceAll(importedRecords);
    return;
  }

  if (importedRecords.length > 0) {
    await memoryStoreService.mergeAll(importedRecords);
  }
}

export async function buildUserDataExportPayload(
  overrides: UserDataExportOverrides = {}
): Promise<UserDataExportPayload> {
  const agentSessions = await storageFacade.readAllStoreEntries(sessionsStore);
  const lastUsedRoles = await storageFacade.readAllStoreEntries(lastUsedRolesStore);
  const memoryRecords = await memoryStoreService.list();

  const localStorageKeysSeen = Object.keys(localStorage);

  const persistedConfigs = safeParseJson<unknown[]>(
    storageFacade.getString(STORAGE_KEYS.configList),
    []
  );

  return {
    schemaVersion: '1.1.0',
    exportedAt: new Date().toISOString(),
    settings: {
      domain: overrides.settings?.currentDomain ?? storageFacade.getCurrentDomain(),
      theme: overrides.settings?.currentTheme ?? storageFacade.getTheme(),
      dataVersion: storageFacade.getDataVersion(),
      aiConfig: {
        activeConfigId: overrides.settings?.activeConfigId ?? storageFacade.getActiveConfigId(),
        configs: cloneSerializable(overrides.settings?.configs ?? persistedConfigs),
      },
      customPrompts: {
        instructions: safeParseArray(storageFacade.getString(STORAGE_KEYS.customInstructions)),
        personas: safeParseArray(storageFacade.getString(STORAGE_KEYS.customPersonas)),
      },
    },
    chat: {
      persistedStores: {
        agentSessions,
        lastUsedRoles,
      },
      liveSnapshot: {
        sessions: cloneSerializable(overrides.chat?.sessions ?? null),
        activeSessionIds: cloneSerializable(overrides.chat?.activeSessionIds ?? null),
        activeInstructionId: overrides.chat?.activeInstructionId ?? null,
      },
    },
    memoryLibrary: {
      implemented: false,
      schemaVersion: '0.1.0',
      records: memoryRecords,
      interfaces: {
        list: null,
        upsert: null,
        remove: null,
      },
      note: 'Memory library is not fully implemented yet. Interface placeholders are reserved.',
    },
    debug: {
      localStorage: {
        keysSeen: localStorageKeysSeen,
        legacy: storageFacade.getLegacyConfigSnapshot(),
      },
    },
  };
}

export async function exportUserData(
  overrides: UserDataExportOverrides = {}
): Promise<UserDataExportResult> {
  const payload = await buildUserDataExportPayload(overrides);
  return downloadJson(payload, 'story-user-data-export');
}

export async function readUserDataImportFile(file: File): Promise<UserDataImportPayload> {
  const text = await file.text();
  const raw = JSON.parse(text);
  return normalizeImportPayload(raw);
}

export function previewUserDataImport(payload: UserDataImportPayload): UserDataImportResult {
  const normalizedPayload = normalizeImportPayload(payload);
  return {
    strategy: 'preview',
    applied: false,
    summary: analyzeImportPayload(normalizedPayload),
    warnings: [],
  };
}

export async function importUserData(
  payload: UserDataImportPayload,
  strategy: Exclude<UserDataImportStrategy, 'preview'>
): Promise<UserDataImportResult> {
  const normalizedPayload = normalizeImportPayload(payload);
  const warnings: string[] = [];

  await applySettingsImport(normalizedPayload, strategy);
  await applyChatImport(normalizedPayload, strategy);
  await applyMemoryImport(normalizedPayload, strategy);

  return {
    strategy,
    applied: true,
    summary: analyzeImportPayload(normalizedPayload),
    warnings,
  };
}

export async function buildMemoryLibraryExportPayload(): Promise<MemoryLibraryExportPayload> {
  return memoryStoreService.list();
}

export async function exportMemoryLibrary(): Promise<UserDataExportResult> {
  const payload = await buildMemoryLibraryExportPayload();
  return downloadJson(payload, 'story-memory-library-export');
}

export async function readMemoryLibraryImportFile(file: File): Promise<MemoryLibraryImportPayload> {
  const text = await file.text();
  const raw = JSON.parse(text);
  if (!Array.isArray(raw)) {
    throw new Error('记忆导入文件格式错误：必须是 JSON 数组。');
  }
  return raw as MemoryLibraryImportPayload;
}

export function previewMemoryLibraryImport(payload: MemoryLibraryImportPayload): MemoryLibraryImportResult {
  const summary = buildMemoryImportSummary(payload);
  const warnings: string[] = [];

  if (summary.memoryRecords === 0) {
    warnings.push('文件中未发现有效记忆记录。');
  }

  return {
    strategy: 'preview',
    applied: false,
    summary,
    warnings,
  };
}

export async function importMemoryLibrary(
  payload: MemoryLibraryImportPayload,
  strategy: Exclude<UserDataImportStrategy, 'preview'>
): Promise<MemoryLibraryImportResult> {
  const summary = buildMemoryImportSummary(payload);
  const warnings: string[] = [];
  const canApply = strategy === 'overwrite' || summary.memoryRecords > 0;

  if (!canApply) {
    warnings.push('未执行导入：没有可用的记忆记录。');
  } else {
    await applyMemoryImportRecords(payload as unknown[], strategy);
  }

  return {
    strategy,
    applied: canApply,
    summary,
    warnings,
  };
}
