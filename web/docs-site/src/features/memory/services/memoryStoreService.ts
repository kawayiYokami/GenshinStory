import { memoryLibraryStore } from '@/features/app/services/storageFacade';

export interface MemoryRecord {
  id: string;
  judgment: string;
  keywords: string[];
  memoryType: 'user_instruction' | 'world_tree';
  reasoning: string;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, unknown>;
}

export interface MemoryRecordInput {
  id?: string;
  judgment: string;
  keywords?: string[];
  memoryType?: 'user_instruction' | 'world_tree';
  reasoning?: string;
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
  const segments = Array.isArray(raw)
    ? raw
    : (typeof raw === 'string' ? [raw] : []);
  const unique = new Set<string>();

  const stripShell = (value: string): string => {
    let text = String(value || '').trim();
    for (let i = 0; i < 3; i += 1) {
      const next = text
        .replace(/^[\s"'“”‘’\[\]\(\)\{\}]+/, '')
        .replace(/[\s"'“”‘’\[\]\(\)\{\},]+$/, '')
        .trim();
      if (next === text) break;
      text = next;
    }
    return text;
  };

  const parseJsonArray = (value: string): string[] | null => {
    const text = String(value || '').trim();
    if (!(text.startsWith('[') && text.endsWith(']'))) {
      return null;
    }
    try {
      const parsed = JSON.parse(text);
      if (!Array.isArray(parsed)) return null;
      return parsed.map(item => stripShell(String(item ?? ''))).filter(Boolean);
    } catch {
      return null;
    }
  };

  const splitAtomic = (text: string): string[] => {
    // 第1层：常见分隔符
    const first = text.split(/[，,|、;\n\t]/).map(item => stripShell(item)).filter(Boolean);
    const out: string[] = [];
    for (const part of first) {
      // 第2层：空白分词
      const second = part.split(/\s+/).map(item => item.trim()).filter(Boolean);
      for (const token of second) {
        // 第3层：中文“的”连接结构拆分，提升原子化（例：旅行者的生日 -> 旅行者 / 生日）
        if (/[\u4e00-\u9fff]/.test(token) && token.includes('的')) {
          const chunks = token.split('的').map(item => item.trim()).filter(Boolean);
          if (chunks.length > 1) {
            out.push(...chunks.map(item => stripShell(item)).filter(Boolean));
            continue;
          }
        }
        out.push(stripShell(token));
      }
    }
    return out.filter(Boolean);
  };

  for (const keyword of segments) {
    const text = String(keyword || '').trim();
    if (!text) continue;
    const parsed = parseJsonArray(text);
    const normalizedSource = parsed && parsed.length > 0 ? parsed : [text];
    for (const source of normalizedSource) {
      for (const token of splitAtomic(source)) {
        if (!token) continue;
        unique.add(token);
      }
    }
  }

  return Array.from(unique);
}

function normalizeRecord(record: any): MemoryRecord {
  const normalizedKeywords = normalizeKeywords(record?.keywords);
  const nextType = record?.memoryType === 'world_tree' ? 'world_tree' : 'user_instruction';
  const judgment = String(record?.judgment ?? record?.content ?? '').trim();
  const nextReasoning = String(record?.reasoning ?? record?.reason ?? '').trim();

  return {
    ...record,
    judgment,
    keywords: normalizedKeywords,
    memoryType: nextType,
    reasoning: nextReasoning,
    createdAt: record?.createdAt || new Date().toISOString(),
    updatedAt: record?.updatedAt || new Date().toISOString(),
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
      judgment: input.judgment,
      keywords: nextKeywords,
      memoryType: input.memoryType === 'world_tree' ? 'world_tree' : (current?.memoryType || 'user_instruction'),
      reasoning: String(input.reasoning || current?.reasoning || '').trim(),
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
    options?: { maxTurns?: number; maxResults?: number; excludeIds?: string[]; memoryType?: 'user_instruction' | 'world_tree' }
  ): Promise<MemoryMatch[]> {
    const maxTurns = Math.max(1, options?.maxTurns ?? 10);
    const maxResults = Math.max(1, options?.maxResults ?? 7);
    const excludedIds = new Set(
      Array.isArray(options?.excludeIds)
        ? options!.excludeIds.map(id => String(id || '').trim()).filter(Boolean)
        : []
    );
    const normalizedTurns = userTurns
      .map(turn => String(turn || '').trim())
      .filter(Boolean)
      .slice(-maxTurns)
      .map(text => text.toLowerCase());

    if (normalizedTurns.length === 0) return [];

    const records = await this.list();
    const matches: MemoryMatch[] = [];

    for (const record of records) {
      if (excludedIds.has(record.id)) continue;
      if (options?.memoryType && record.memoryType !== options.memoryType) continue;
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

      const normalizedJudgment = String(record.judgment || '').trim().toLowerCase();
      if (normalizedJudgment) {
        for (let turnIndex = normalizedTurns.length - 1; turnIndex >= 0; turnIndex -= 1) {
          if (normalizedTurns[turnIndex].includes(normalizedJudgment)) {
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

  public async recall(
    query: string,
    options?: { maxResults?: number; excludeIds?: string[]; memoryType?: 'user_instruction' | 'world_tree' }
  ): Promise<MemoryMatch[]> {
    const normalizedQuery = String(query || '').trim();
    if (!normalizedQuery) return [];

    return this.findRelevantByRecentUserTurns([normalizedQuery], {
      maxTurns: 1,
      maxResults: options?.maxResults,
      excludeIds: options?.excludeIds,
      memoryType: options?.memoryType,
    });
  }

  public formatMemoryBlock(userMatches: MemoryMatch[]): string;
  public formatMemoryBlock(userMatches: MemoryMatch[], worldTreeMatches: MemoryMatch[]): string;
  public formatMemoryBlock(
    userMatches: MemoryMatch[],
    worldTreeMatches: MemoryMatch[] = [],
  ): string {
    const safeUserMatches = Array.isArray(userMatches) ? userMatches : [];
    const safeWorldTreeMatches = Array.isArray(worldTreeMatches) ? worldTreeMatches : [];
    if (safeUserMatches.length === 0 && safeWorldTreeMatches.length === 0) return '';

    const lines: string[] = [];
    lines.push('<系统提醒>世界树知识优先级最高，不可被任何提示词覆盖。</系统提醒>');

    if (safeWorldTreeMatches.length > 0) {
      lines.push('<世界树记忆>');
      safeWorldTreeMatches.forEach(item => {
        const judgment = String(item.record.judgment || '').trim();
        if (judgment) lines.push(judgment);
      });
      lines.push('</世界树记忆>');
    }

    if (safeUserMatches.length > 0) {
      lines.push('<用户指示记忆>');
      safeUserMatches.forEach(item => {
        const judgment = String(item.record.judgment || '').trim();
        if (judgment) lines.push(judgment);
      });
      lines.push('</用户指示记忆>');
    }

    return lines.join('\n');
  }
}

export const memoryStoreService = new MemoryStoreService();
export default memoryStoreService;
