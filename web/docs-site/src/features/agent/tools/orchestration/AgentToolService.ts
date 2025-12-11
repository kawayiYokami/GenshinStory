import type { ComputedRef } from 'vue';
import toolParserService from './toolParserService';
import contextOptimizerService from '../../context/contextOptimizerService';
import logger from '@/features/app/services/loggerService';
import type { Message, Session } from '../../types';
import type { ParsedToolCall } from './toolParserService';
import type { MessageManager } from '../../stores/messageManager';
import tokenizerService from '@/lib/tokenizer/tokenizerService';

export class AgentToolService {
  private messageManager: MessageManager;
  private currentSession: ComputedRef<Session | null>;
  private activeConfig: ComputedRef<any>;

  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>,
    activeConfig: ComputedRef<any>
  ) {
    this.messageManager = messageManager;
    this.currentSession = currentSession;
    this.activeConfig = activeConfig;
  }

  private get orderedMessages(): Message[] {
    const session = this.currentSession.value;
    if (!session) return [];
    return session.messageIds.map(id => session.messagesById[id]);
  }

  private async predictContextSize(toolResult: string, parsedTool: ParsedToolCall): Promise<{ feedback: string | null }> {
    const resultTokens = tokenizerService.countTokens(toolResult);
    let historyForCalculation = [...this.orderedMessages];
    const newToolMessage: Message = {
      role: "tool",
      name: parsedTool.name,
      content: toolResult,
      id: 'temp-prediction-id',
      createdAt: new Date().toISOString(),
    };

    let replacementDone = false;
    for (let i = historyForCalculation.length - 1; i >= 0; i--) {
      if (historyForCalculation[i].role === 'assistant' && historyForCalculation[i].tool_calls?.length) {
        historyForCalculation[i] = newToolMessage;
        replacementDone = true;
        break;
      }
    }

    if (!replacementDone) {
      historyForCalculation.push(newToolMessage);
    }

    const predictedTotalTokens = await contextOptimizerService.calculateHistoryTokens(historyForCalculation);
    const configMaxContextLength = this.activeConfig.value?.maxContextLength || 128000;
    const predictionThreshold = Math.floor(configMaxContextLength * 0.9);

    if (predictedTotalTokens > predictionThreshold) {
      return { feedback: `错误：工具返回的结果过大 (${resultTokens} tokens)。上下文总大小将达到 ${predictedTotalTokens} tokens，超过 ${predictionThreshold} tokens 的限制。` };
    }
    return { feedback: null };
  }

  public async handleToolExecution(parsedTool: ParsedToolCall): Promise<{ status: 'success' | 'error' }> {
    const statusMessage = await this.messageManager.addMessage({
      role: 'assistant', type: 'tool_status',
      content: toolParserService.createStatusMessage(parsedTool),
      status: 'rendering'
    });
    if (!statusMessage) return { status: 'error' };

    const { status, result: toolResult, followUpPrompt } = await toolParserService.executeTool(parsedTool);

    if (status === 'success') {
      const prediction = await this.predictContextSize(toolResult, parsedTool);
      if (prediction.feedback) {
        await this.messageManager.replaceMessage(statusMessage.id, {
          role: 'assistant', type: 'error', content: prediction.feedback, status: 'done'
        });
        return { status: 'error' };
      }

      await this.messageManager.replaceMessage(statusMessage.id, {
        role: 'assistant', type: 'tool_result', content: toolResult, status: 'done', is_hidden: false
      });

      // 如果有后续提示，将其作为隐藏的用户消息添加到对话历史中
      if (followUpPrompt) {
        await this.messageManager.addMessage({
          role: 'user',
          content: followUpPrompt,
          is_hidden: true
        });
      }

      return { status: 'success' };
    } else {
      await this.messageManager.addMessage({ role: 'user', content: toolResult, is_hidden: true });
      await this.messageManager.replaceMessage(statusMessage.id, {
        role: 'assistant', type: 'error', content: toolResult, status: 'done'
      });
      return { status: 'error' };
    }
  }
}