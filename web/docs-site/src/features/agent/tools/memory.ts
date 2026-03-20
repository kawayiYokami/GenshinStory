import type { Tool, ToolExecutionResult } from './tool';
import logger from '../../app/services/loggerService';
import memoryStoreService from '@/features/memory/services/memoryStoreService';
import worldTreeMemoryService from '@/features/memory/services/worldTreeMemoryService';

interface MemoryToolParams {
  action?: 'add' | 'remove' | 'recall';
  id?: string;
  judgment?: string;
  keywords?: string[] | string;
  query?: string;
  topK?: number;
  memoryType?: 'user_instruction' | 'world_tree';
  reasoning?: string;
  derivedFrom?: 'user' | 'document';
}

function normalizeKeywords(input: string[] | string | undefined): string[] {
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

  const splitByDelimiters = (value: string): string[] => {
    return value
      .split(/[，,|、;\n]/)
      .map(item => stripShell(item))
      .filter(Boolean);
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

  const segments = Array.isArray(input)
    ? input.map(item => String(item || '').trim()).filter(Boolean)
    : (typeof input === 'string' ? [input] : []);

  const unique = new Set<string>();
  for (const segment of segments) {
    const parsed = parseJsonArray(segment);
    if (parsed && parsed.length > 0) {
      parsed.forEach(token => unique.add(token));
      continue;
    }
    splitByDelimiters(segment).forEach(token => unique.add(token));
  }

  return Array.from(unique);
}

const memoryTool: Tool<MemoryToolParams> = {
  name: 'memory',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: MemoryToolParams): Promise<ToolExecutionResult> {
    const action = params.action || 'add';

    try {
      if (action === 'recall') {
        const query = String(params.query || params.judgment || '').trim();
        if (!query) {
          return { result: '错误: memory.recall 缺少 query 参数。' };
        }

        const topK = Number.isFinite(params.topK) ? Math.max(1, Math.floor(Number(params.topK))) : 7;
        const userMatches = await memoryStoreService.recall(query, { maxResults: topK, memoryType: 'user_instruction' });
        const worldTreeMatches = await worldTreeMemoryService.recall(query, topK);
        const userRecords = userMatches.map(item => item.record);
        const worldTreeRecords = worldTreeMatches.map(item => item.record);
        const records = [...worldTreeRecords, ...userRecords];

        return {
          result: JSON.stringify({
            tool: 'memory',
            action: 'recall',
            query,
            total: records.length,
            userInstructionTotal: userRecords.length,
            worldTreeTotal: worldTreeRecords.length,
            userInstructionRecords: userRecords,
            worldTreeRecords,
            records,
          }, null, 2),
        };
      }

      if (action === 'remove') {
        const id = String(params.id || '').trim();
        if (!id) {
          return { result: '错误: memory.remove 缺少 id 参数。' };
        }

        const removed = await memoryStoreService.remove(id);
        await worldTreeMemoryService.remove(id);
        return {
          result: JSON.stringify({
            tool: 'memory',
            action: 'remove',
            id,
            removed,
            message: removed ? '记忆已删除。' : '未找到对应记忆。',
          }, null, 2),
        };
      }

      const judgment = String(params.judgment || '').trim();
      if (!judgment) {
        return { result: '错误: memory.add 缺少 judgment 参数。' };
      }

      const keywords = normalizeKeywords(params.keywords);
      if (keywords.length === 0) {
        return { result: '错误: memory.add 需要至少一个关键词 keywords。' };
      }

      const reasoning = String(params.reasoning || '').trim();
      if (reasoning.length > 500) {
        return { result: '错误: memory.add 的 reasoning 过长，请保持极简。' };
      }

      const derivedFrom = params.derivedFrom === 'document' ? 'document' : 'user';
      const requestedType = params.memoryType === 'world_tree' ? 'world_tree' : 'user_instruction';
      const memoryType = derivedFrom === 'document' ? requestedType : 'user_instruction';
      const downgraded = requestedType === 'world_tree' && memoryType !== requestedType;

      // Check if there's an existing record to detect memoryType changes
      let previousRecord: { memoryType: string } | null = null;
      if (params.id) {
        try {
          const existing = await memoryStoreService.recall(params.id, { maxResults: 1 });
          if (existing.length > 0) {
            previousRecord = existing[0].record;
          }
        } catch {
          // Ignore recall errors for non-existent records
        }
      }

      const record = await memoryStoreService.upsert({
        id: params.id ? String(params.id).trim() : undefined,
        judgment,
        keywords,
        reasoning,
        memoryType,
      });

      // Handle world_tree service sync: remove stale entries if type changed from world_tree
      if (previousRecord?.memoryType === 'world_tree' && record.memoryType !== 'world_tree') {
        await worldTreeMemoryService.remove(record.id);
      } else if (record.memoryType === 'world_tree') {
        await worldTreeMemoryService.upsert(record);
      }

      return {
        result: JSON.stringify({
          tool: 'memory',
          action: 'add',
          message: downgraded
            ? '记忆已保存。该内容来源于用户输入，已按规则归类为 user_instruction。'
            : '关键记忆已保存。',
          record,
        }, null, 2),
      };
    } catch (error: any) {
      logger.error('工具 memory 发生意外异常:', error);
      return {
        result: "错误: 工具 'memory' 内部执行失败。请检查参数后重试。",
      };
    }
  },
};

export default memoryTool;
