import logger from '../../app/services/loggerService';
import yaml from 'js-yaml';
import type { Tool, PromptTrigger } from './tool';

// 需要忽略的非工具文件列表
const IGNORED_FILES = [
  './tool.ts',
  './toolRegistryService.ts', 
  './toolStateService.ts'
];

class ToolRegistryService {
  private tools: Map<string, Tool> = new Map();
  private loaded = false;

  async loadTools(): Promise<void> {
    if (this.loaded) return;

    // 动态导入所有工具模块
    const toolModules = import.meta.glob('./*.ts', { eager: true });
    
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

  getToolNames(): string[] {
    return Array.from(this.tools.keys());
  }

  /**
   * 获取所有应在初始系统提示中提供的工具
   */
  getInitialSystemTools(): Tool[] {
    return Array.from(this.tools.values()).filter(tool => 
      tool.prompt_trigger === 'system'
    );
  }

  /**
   * 获取所有应在指定工具执行后作为后续提示提供的工具
   * @param toolName 前置工具名称
   */
  getFollowUpTools(toolName: string): Tool[] {
    return Array.from(this.tools.values()).filter(tool => {
      if (typeof tool.prompt_trigger === 'object' && tool.prompt_trigger && tool.prompt_trigger.on_tool_result) {
        return tool.prompt_trigger.on_tool_result.includes(toolName);
      }
      return false;
    });
  }
}

export const toolRegistryService = new ToolRegistryService();
export default toolRegistryService;