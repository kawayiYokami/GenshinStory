import type { Tool, ToolExecutionResult } from './tool';
import logger from '../../app/services/loggerService';
import memoryStoreService from '@/features/memory/services/memoryStoreService';

interface MemoryToolParams {
  action?: 'add' | 'remove' | 'list';
  id?: string;
  content?: string;
  keywords?: string[] | string;
}

function normalizeKeywords(input: string[] | string | undefined): string[] {
  if (Array.isArray(input)) {
    return Array.from(new Set(input.map(item => String(item || '').trim()).filter(Boolean)));
  }

  if (typeof input === 'string') {
    return Array.from(new Set(
      input
        .split(/[，,|、;\n]/)
        .map(item => item.trim())
        .filter(Boolean)
    ));
  }

  return [];
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
      if (action === 'list') {
        const records = await memoryStoreService.list();
        return {
          result: JSON.stringify({
            tool: 'memory',
            action: 'list',
            total: records.length,
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

      const content = String(params.content || '').trim();
      if (!content) {
        return { result: '错误: memory.add 缺少 content 参数。' };
      }

      const keywords = normalizeKeywords(params.keywords);
      if (keywords.length === 0) {
        return { result: '错误: memory.add 需要至少一个关键词 keywords。' };
      }

      const record = await memoryStoreService.upsert({
        id: params.id ? String(params.id).trim() : undefined,
        content,
        keywords,
      });

      return {
        result: JSON.stringify({
          tool: 'memory',
          action: 'add',
          message: '关键记忆已保存。',
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

