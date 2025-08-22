// web/docs-site/src/features/agent/tools/toolStateService.ts

/**
 * 工具状态服务 - 管理工具提示的发送状态
 * 用于确保每个反应式提示只发送一次
 */
class ToolStateService {
  private promptSentStates: Map<string, boolean> = new Map();

  /**
   * 检查指定工具的提示是否已被发送
   * @param toolName 工具名称
   * @returns 提示是否已发送
   */
  hasPromptBeenSent(toolName: string): boolean {
    return this.promptSentStates.get(toolName) || false;
  }

  /**
   * 标记指定工具的提示为已发送
   * @param toolName 工具名称
   */
  markPromptAsSent(toolName: string): void {
    this.promptSentStates.set(toolName, true);
  }

  /**
   * 重置所有工具的提示发送状态
   * 在对话历史被压缩时调用
   */
  resetAllPromptStates(): void {
    this.promptSentStates.clear();
  }

  /**
   * 获取所有工具状态的副本（用于调试）
   */
  getStatesCopy(): Map<string, boolean> {
    return new Map(this.promptSentStates);
  }
}

// 导出单例实例
export const toolStateService = new ToolStateService();
export default toolStateService;