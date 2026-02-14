/**
 * @fileoverview 代理API服务类
 * @description 负责与AI API进行通信，处理API调用和流式响应
 */
import type { ComputedRef } from 'vue';
import logger from '@/features/app/services/loggerService';
import type { Message, ProtocolMode } from '@/features/agent/types';
import type { MessageManager } from '@/features/agent/stores/messageManager';
import { AgentProtocolRuntime } from './provider/AgentProtocolRuntime';
import { AgentStreamProjector } from './stream/AgentStreamProjector';

/**
 * handleStream 返回结果
 */
export interface StreamResult {
  assistantMessage: Message | null;
  finishReason: string;
  steps: any[];
}

/**
 * 代理API服务类
 * @description 提供与AI API交互的功能
 */
export class AgentApiService {
  private protocolRuntime: AgentProtocolRuntime;
  private messageManager: MessageManager;

  constructor(
    messageManager: MessageManager,
    activeConfig: ComputedRef<any>
  ) {
    this.messageManager = messageManager;
    this.protocolRuntime = new AgentProtocolRuntime(activeConfig);
  }

  /**
   * 调用AI API
   * @description 向AI API发送聊天完成请求
   */
  public async callApi(history: Message[], signal: AbortSignal): Promise<{ result: any; protocolMode: ProtocolMode }> {
    return this.protocolRuntime.callApi(history, signal);
  }

  /**
   * 处理 AI 响应流
   * @description 消费 fullStream，更新 UI（文本、工具状态、工具结果）
   */
  public async handleStream(result: any, abortSignal: AbortSignal): Promise<StreamResult> {
    const projector = new AgentStreamProjector(this.messageManager);
    logger.log('[AgentApiService] 开始消费 fullStream...');

    try {
      if (result?.fullStream && Symbol.asyncIterator in Object(result.fullStream)) {
        for await (const part of result.fullStream) {
          if (abortSignal.aborted) {
            logger.warn('[AgentApiService] fullStream 消费被中止。');
            break;
          }
          await projector.consumePart(part);
        }
      }
    } catch (err: any) {
      if (err?.name === 'AI_NoOutputGeneratedError') {
        logger.warn('[AgentApiService] 流无文本输出（纯工具调用场景）');
      } else {
        logger.error('[AgentApiService] 消费 fullStream 时发生错误:', err);
        await projector.markCurrentMessageAsError();
        throw err;
      }
    }

    let finishReason = 'unknown';
    let steps: any[] = [];

    try {
      finishReason = await result.finishReason;
      steps = await result.steps || [];
      logger.log(`[AgentApiService] 流完成: finishReason=${finishReason}, steps=${steps.length}`);
    } catch (e) {
      logger.warn('[AgentApiService] 获取 finishReason/steps 失败:', e);
    }

    try {
      await projector.backfillToolMessagesFromSteps(result, steps);
    } catch (e) {
      logger.warn('[AgentApiService] 从 steps 回填工具消息失败:', e);
    }

    await projector.finalize(result);
    return { assistantMessage: projector.getAssistantMessage(), finishReason, steps };
  }
}
