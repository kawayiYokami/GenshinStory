import { memoryLibraryStore } from '@/features/app/services/storageFacade';

export interface MemoryRecord {
  id: string;
  content: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, unknown>;
}

export interface MemoryRecordInput {
  id?: string;
  content: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface MemoryLibraryAdapter {
  list(): Promise<MemoryRecord[]>;
  upsert(input: MemoryRecordInput): Promise<MemoryRecord>;
  remove(id: string): Promise<boolean>;
}

const MEMORY_RECORDS_KEY = 'records';

function normalizeRecord(record: MemoryRecord): MemoryRecord {
  return {
    ...record,
    tags: Array.isArray(record.tags) ? record.tags : [],
    createdAt: record.createdAt || new Date().toISOString(),
    updatedAt: record.updatedAt || new Date().toISOString(),
  };
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
  return JSON.parse(JSON.stringify(value)) as T;
}

class MemoryStoreService implements MemoryLibraryAdapter {
  public async list(): Promise<MemoryRecord[]> {
    const records = await memoryLibraryStore.getItem<MemoryRecord[]>(MEMORY_RECORDS_KEY);
    if (!Array.isArray(records)) return [];
    return records.map(normalizeRecord);
  }

  public async upsert(input: MemoryRecordInput): Promise<MemoryRecord> {
    const records = await this.list();
    const now = new Date().toISOString();
    const id = input.id || `memory_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

    const index = records.findIndex(record => record.id === id);
    const current = index >= 0 ? records[index] : null;

    const nextRecord: MemoryRecord = {
      id,
      content: input.content,
      tags: Array.isArray(input.tags) ? input.tags : (current?.tags || []),
      metadata: input.metadata ?? current?.metadata,
      createdAt: current?.createdAt || now,
      updatedAt: now,
    };

    if (index >= 0) {
      records[index] = nextRecord;
    } else {
      records.push(nextRecord);
    }

    await memoryLibraryStore.setItem(MEMORY_RECORDS_KEY, records);
    return nextRecord;
  }

  public async remove(id: string): Promise<boolean> {
    const records = await this.list();
    const next = records.filter(record => record.id !== id);
    if (next.length === records.length) return false;
    await memoryLibraryStore.setItem(MEMORY_RECORDS_KEY, next);
    return true;
  }

  public async replaceAll(records: MemoryRecord[]): Promise<void> {
    const normalized = Array.isArray(records) ? records.map(normalizeRecord) : [];
    await memoryLibraryStore.setItem(MEMORY_RECORDS_KEY, normalized);
  }

  public async mergeAll(records: MemoryRecord[]): Promise<MemoryRecord[]> {
    const existing = await this.list();
    const byId = new Map(existing.map(record => [record.id, record] as const));

    for (const record of records) {
      byId.set(record.id, normalizeRecord(record));
    }

    const merged = Array.from(byId.values());
    await memoryLibraryStore.setItem(MEMORY_RECORDS_KEY, merged);
    return cloneSerializable(merged);
  }
}

export const memoryStoreService = new MemoryStoreService();
export default memoryStoreService;

