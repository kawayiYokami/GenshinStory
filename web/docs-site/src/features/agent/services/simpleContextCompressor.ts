import type { Message, MessageContentPart } from '../types';

/**
 * 简化的上下文压缩服务
 * 使用确定性逻辑替代复杂的AI摘要，提供快速、可靠的上下文压缩
 */
export class SimpleContextCompressor {
  /**
   * 压缩消息列表
   * @param messages 原始消息列表
   * @returns 压缩后的消息列表
   */
  async compressMessages(messages: Message[]): Promise<Message[]> {
    // 1. 分离系统消息和其他消息
    const systemMessage = messages.find(m => m.role === 'system');
    const nonSystemMessages = messages.filter(m => m.role !== 'system');

    // 2. 如果非系统消息少于等于5条，直接返回原消息（无需压缩）
    if (nonSystemMessages.length <= 5) {
      return messages;
    }

    // 3. 保留最后5条非系统消息
    const recentMessages = nonSystemMessages.slice(-5);

    // 4. 从被省略的消息生成摘要
    const omittedMessages = nonSystemMessages.slice(0, -5);
    const summary = this.generateSimpleSummary(omittedMessages);

    // 5. 构建新的消息列表
    const compressedMessages: Message[] = [];

    // 添加系统消息（如果有）
    if (systemMessage) {
      compressedMessages.push(systemMessage);
    }

    // 添加摘要消息
    compressedMessages.push({
      role: 'user',
      content: `[对话摘要] ${summary}`,
      id: `summary_${Date.now()}`,
      createdAt: new Date().toISOString()
    });

    // 添加最近的消息
    compressedMessages.push(...recentMessages);

    return compressedMessages;
  }

  /**
   * 生成简单的对话摘要
   * @param messages 消息列表
   * @returns 摘要文本
   */
  private generateSimpleSummary(messages: Message[]): string {
    const userCount = messages.filter(m => m.role === 'user').length;
    const assistantCount = messages.filter(m => m.role === 'assistant').length;
    const toolCallCount = messages.filter(m => m.role === 'tool').length;

    // 获取第一条用户消息的主题（如果有内容的话）
    const firstUserMessage = messages.find(m => m.role === 'user' && m.content);
    let topicHint = '未指定主题';

    if (firstUserMessage && firstUserMessage.content) {
      if (typeof firstUserMessage.content === 'string') {
        topicHint = firstUserMessage.content.slice(0, 50) +
                   (firstUserMessage.content.length > 50 ? '...' : '');
      } else if (Array.isArray(firstUserMessage.content)) {
        // 处理 MessageContentPart[] 类型
        const textPart = firstUserMessage.content.find(part => part.type === 'text' && part.text);
        if (textPart && textPart.text) {
          topicHint = textPart.text.slice(0, 50) +
                     (textPart.text.length > 50 ? '...' : '');
        }
      }
    }

    return `本次对话关于"${topicHint}"，包含${userCount}条用户消息、${assistantCount}条助手回复和${toolCallCount}次工具调用记录。`;
  }

  /**
   * 计算消息列表的token数量
   * @param messages 消息列表
   * @returns token数量
   */
  calculateTokens(messages: Message[]): number {
    // 这里需要使用实际的tokenizer服务
    // 暂时使用简单的字符数估算
    const text = messages.map(m => {
      if (!m.content) return '';

      if (typeof m.content === 'string') {
        return m.content;
      }

      if (Array.isArray(m.content)) {
        // 处理 MessageContentPart[] 类型
        return m.content
          .filter(part => part.type === 'text' && part.text)
          .map(part => (part as MessageContentPart & { text: string }).text)
          .join(' ');
      }

      return '';
    }).join('\n');

    // 简单估算：4个字符约等于1个token（这是一个粗略估算）
    return Math.ceil(text.length / 4);
  }
}

// 导出单例实例
export const simpleContextCompressor = new SimpleContextCompressor();