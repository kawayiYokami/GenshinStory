import logger from '../../../app/services/loggerService';
import yaml from 'js-yaml';
import type { Tool } from '../tool';
import { tool as createAiTool } from 'ai';
import { z } from 'zod';

// 需要忽略的非工具文件列表
const IGNORED_FILES = [
  '../tool.ts',
  '../__tests__/',
  '../implementations/',
  '../orchestration/',
  '../registry/'
];

// Zod schema 定义
const toolSchemas: Record<string, z.ZodObject<any>> = {
  search_docs: z.object({
    query: z.string().optional(),
    regex: z.string().optional(),
    path: z.string().optional(),
    limit: z.number().optional(),
    maxResults: z.number().optional(),
  }),
  read_doc: z.object({
    path: z.string().optional(),
    target: z.string().optional(),
    line_range: z.string().optional(),
  }),
  explore: z.object({
    tasks: z.array(z.string()),
    maxToolCalls: z.number().optional(),
  }),
  ask_choice: z.object({
    question: z.string(),
    suggestions: z.array(z.string()).optional(),
  }),
};

class ToolRegistryService {
  private tools: Map<string, Tool> = new Map();
  private loaded = false;

  async loadTools(): Promise<void> {
    if (this.loaded) return;

    // 动态导入所有工具模块
    const toolModules = import.meta.glob('../*.ts', { eager: true });

    for (const [path, module] of Object.entries(toolModules)) {
      if (IGNORED_FILES.includes(path)) continue;

      try {
        const tool = (module as any).default;
        if (tool && typeof tool.name === 'string' && typeof tool.execute === 'function') {
          // 加载对应的YAML配置文件，如果加载失败则不注册该工具
          const yamlLoaded = await this.loadToolYamlConfig(tool.name, tool);
          if (yamlLoaded) {
            this.tools.set(tool.name, tool);
            logger.log(`已注册工具: ${tool.name}`);
          } else {
            logger.error(`工具 ${tool.name} 的YAML配置加载失败，跳过注册`);
          }
        }
      } catch (error) {
        logger.error(`加载工具模块失败: ${path}`, error);
      }
    }

    this.loaded = true;
    logger.log('所有工具加载完成', { loadedTools: Array.from(this.tools.keys()) });
  }

  private async loadToolYamlConfig(toolName: string, toolInstance: any): Promise<boolean> {
    try {
      const v = Date.now();
      const response = await fetch(`/prompts/tools/${toolName}.yaml?v=${v}`);

      if (!response.ok) {
        logger.error(`无法加载工具 ${toolName} 的YAML配置文件: ${response.status} ${response.statusText}`);
        return false;
      }

      const yamlText = await response.text();
      const config = yaml.load(yamlText) as any;

      // 更新工具实例的元数据
      if (config.type) toolInstance.type = config.type;
      if (config.description) toolInstance.description = config.description;
      if (config.usage) toolInstance.usage = config.usage;
      if (config.examples) toolInstance.examples = config.examples;
      if (config.error_guidance) toolInstance.error_guidance = config.error_guidance;
      if (config.prompt_trigger) toolInstance.prompt_trigger = config.prompt_trigger;

      return true;

    } catch (error) {
      logger.error(`加载工具 ${toolName} 的YAML配置时出错:`, error);
      return false;
    }
  }

  getTool(name: string): Tool | null {
    return this.tools.get(name) || null;
  }

  getAllTools(): Tool[] {
    return Array.from(this.tools.values());
  }

  getExecutionTools(): Tool[] {
    return this.getAllTools().filter(tool => tool.type === 'execution');
  }

  getToolNames(): string[] {
    return Array.from(this.tools.keys());
  }

  /**
   * 获取工具的 Zod schema
   */
  private getSchema(toolName: string): z.ZodObject<any> {
    return toolSchemas[toolName] || z.object({}).passthrough();
  }

  /**
   * 转换为 AI SDK 工具定义
   * - 执行工具 (execution): 包含 execute 函数，SDK 自动执行
   * - UI 工具 (ui): 不包含 execute 函数，SDK 在调用时停止
   */
  toSdkToolDefinitions(options?: { excludedTools?: string[]; includedTools?: string[] }): Record<string, any> {
    const excluded = new Set(options?.excludedTools || []);
    const included = options?.includedTools ? new Set(options.includedTools) : null;
    const allTools = this.getAllTools().filter(tool => {
      if (excluded.has(tool.name)) return false;
      if (included && !included.has(tool.name)) return false;
      return true;
    });
    const result: Record<string, any> = {};

    for (const tool of allTools) {
      const schema = this.getSchema(tool.name);

      if (tool.type === 'execution') {
        // 执行工具：添加 execute 函数包装器，SDK 自动执行
        result[tool.name] = createAiTool({
          description: tool.description || '',
          inputSchema: schema,
          execute: async (params: any) => {
            logger.log(`[ToolRegistry] SDK 自动执行工具: ${tool.name}`, params);
            const executionResult = await tool.execute(params);
            return executionResult.result;
          },
        });
      } else {
        // UI 工具：不添加 execute 函数，SDK 在调用时停止
        result[tool.name] = createAiTool({
          description: tool.description || '',
          inputSchema: schema,
          // 无 execute 函数，SDK 会在遇到此工具调用时停止
        });
      }
    }

    return result;
  }
}

export const toolRegistryService = new ToolRegistryService();
export default toolRegistryService;
