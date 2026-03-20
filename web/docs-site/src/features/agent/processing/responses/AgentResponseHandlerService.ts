/**
 * @fileoverview 响应处理服务
 * @description 处理 AI 响应的后处理
 *
 * 注意：简化语法（表情、问题、思维链）的解析已移至前端 MessageBubble.vue
 * 此服务仅用于兼容性和未来扩展
 */

import { type ComputedRef } from 'vue';
import logger from '@/features/app/services/loggerService';
import type { Message, Session } from '@/features/agent/types';
import type { MessageManager } from '@/features/agent/stores/messageManager';

export type HandleResponseResult =
  | { type: 'complete' }
  | { type: 'no_op' };

export class AgentResponseHandlerService {
  private messageManager: MessageManager;
  private currentSession: ComputedRef<Session | null>;

  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>
  ) {
    this.messageManager = messageManager;
    this.currentSession = currentSession;
  }

  /**
   * 处理 API 响应
   * 简化语法的解析已移至前端，此方法仅做最终状态更新
   */
  public async handleApiResponse(assistantMessage: Message): Promise<HandleResponseResult> {
    const updatedMessage = this.currentSession.value?.messagesById[assistantMessage.id];
    if (!updatedMessage) {
      logger.warn('[AgentResponseHandlerService] 消息未找到:', assistantMessage.id);
      return { type: 'no_op' };
    }

    // 确保消息状态为完成
    await this.messageManager.updateMessage({
      messageId: assistantMessage.id,
      updates: {
        status: 'done',
      },
    });

    return { type: 'complete' };
  }

  /**
   * 处理 ask_choice UI 工具调用（Structured 模式兼容）
   * @deprecated 简化语法已在前端处理，此方法保留用于兼容
   */
  public async handleAskChoice(
    assistantMessage: Message,
    askChoiceCall: any
  ): Promise<void> {
    logger.log('[AgentResponseHandlerService] ask_choice 已在前端处理，跳过');
  }
}
