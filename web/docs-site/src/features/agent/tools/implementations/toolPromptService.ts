import logger from '../../../app/services/loggerService';
import { toolRegistryService } from '../registry/toolRegistryService';

class ToolPromptService {
  private loaded = false;

  async loadToolPrompts(): Promise<void> {
    if (this.loaded) return;

    // 加载工具注册表中的所有工具
    await toolRegistryService.loadTools();
    this.loaded = true;
    logger.log('工具提示词加载完成');
  }

  getSystemPrompt(): string {
    // 仅将可执行工具添加到系统提示中（UI 协议型工具不对模型暴露）
    const tools = toolRegistryService.getExecutionTools();
    if (tools.length === 0) {
      return '';
    }

    let systemPrompt = '\n\n';
    systemPrompt += 'You have access to a set of tools that are executed upon the user\'s approval. ';
    systemPrompt += 'You can use one tool per message, and the result of the tool\'s execution will be returned in the user\'s response. ';
    systemPrompt += 'You must use the tools step-by-step to accomplish a task, with each tool use being informed by the result of the previous one.\n\n';
    systemPrompt += 'AVAILABLE TOOLS\n\n';

    for (const tool of tools) {
      systemPrompt += `${tool.name}\n`;
      systemPrompt += `Description: ${tool.description}\n`;
      systemPrompt += `Usage:\n${tool.usage}\n`;

      if (tool.examples && tool.examples.length > 0) {
        systemPrompt += `Examples:\n`;
        tool.examples.forEach((example: string) => {
          systemPrompt += `- ${example}\n`;
        });
      }

      systemPrompt += `Error Guidance: ${tool.error_guidance}\n\n`;
    }

    return systemPrompt;
  }
}

export const toolPromptService = new ToolPromptService();
export default toolPromptService;
