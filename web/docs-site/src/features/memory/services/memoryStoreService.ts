import { memoryLibraryStore } from '@/features/app/services/storageFacade';

export interface MemoryRecord {
  id: string;
  content: string;
  keywords: string[];
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, unknown>;
}

export interface MemoryRecordInput {
  id?: string;
  content: string;
  keywords?: string[];
  metadata?: Record<string, unknown>;
}

export interface MemoryMatch {
  record: MemoryRecord;
  hitCount: number;
  lastHitTurnIndex: number;
}

export interface MemoryLibraryAdapter {
  list(): Promise<MemoryRecord[]>;
  upsert(input: MemoryRecordInput): Promise<MemoryRecord>;
  remove(id: string): Promise<boolean>;
}

const MEMORY_RECORDS_KEY = 'records';

function normalizeKeywords(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  const unique = new Set<string>();

  for (const keyword of raw) {
    const text = String(keyword || '').trim();
    if (!text) continue;
    unique.add(text);
  }

  return Array.from(unique);
}

function normalizeRecord(record: MemoryRecord): MemoryRecord {
  const normalizedKeywords = normalizeKeywords(record.keywords);

  return {
    ...record,
    keywords: normalizedKeywords,
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
    const nextKeywords = normalizeKeywords(
      Array.isArray(input.keywords) && input.keywords.length > 0
        ? input.keywords
        : current?.keywords
    );

    const nextRecord: MemoryRecord = {
      id,
      content: input.content,
      keywords: nextKeywords,
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

  public async findRelevantByRecentUserTurns(
    userTurns: string[],
    options?: { maxTurns?: number; maxResults?: number }
  ): Promise<MemoryMatch[]> {
    const maxTurns = Math.max(1, options?.maxTurns ?? 10);
    const maxResults = Math.max(1, options?.maxResults ?? 7);
    const normalizedTurns = userTurns
      .map(turn => String(turn || '').trim())
      .filter(Boolean)
      .slice(-maxTurns)
      .map(text => text.toLowerCase());

    if (normalizedTurns.length === 0) return [];

    const records = await this.list();
    const matches: MemoryMatch[] = [];

    for (const record of records) {
      if (!record.keywords || record.keywords.length === 0) continue;

      let hitCount = 0;
      let lastHitTurnIndex = -1;

      for (const keyword of record.keywords) {
        const normalizedKeyword = String(keyword || '').trim().toLowerCase();
        if (!normalizedKeyword) continue;

        for (let turnIndex = normalizedTurns.length - 1; turnIndex >= 0; turnIndex -= 1) {
          if (normalizedTurns[turnIndex].includes(normalizedKeyword)) {
            hitCount += 1;
            if (turnIndex > lastHitTurnIndex) {
              lastHitTurnIndex = turnIndex;
            }
            break;
          }
        }
      }

      if (hitCount >= 1) {
        matches.push({ record, hitCount, lastHitTurnIndex });
      }
    }

    matches.sort((left, right) => {
      if (right.hitCount !== left.hitCount) {
        return right.hitCount - left.hitCount;
      }
      if (right.lastHitTurnIndex !== left.lastHitTurnIndex) {
        return right.lastHitTurnIndex - left.lastHitTurnIndex;
      }
      return new Date(right.record.updatedAt).getTime() - new Date(left.record.updatedAt).getTime();
    });

    return matches.slice(0, maxResults);
  }

  public formatMemoryBlock(matches: MemoryMatch[]): string {
    if (!Array.isArray(matches) || matches.length === 0) return '';

    const lines: string[] = [];
    lines.push('<系统提醒>历史记忆仅供参考；若与当前证据冲突，以当前证据为准。</系统提醒>');
    lines.push('<记忆>');

    matches.forEach(item => {
      const content = String(item.record.content || '').trim();
      if (content) {
        lines.push(content);
      }
    });

    if (lines.length === 2) return '';

    lines.push('</记忆>');
    return lines.join('\n');
  }
}

export const memoryStoreService = new MemoryStoreService();
export default memoryStoreService;
