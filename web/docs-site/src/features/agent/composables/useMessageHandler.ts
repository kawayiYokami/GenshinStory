import { ref, computed, type Ref, type ComputedRef } from 'vue';
import { storeToRefs } from 'pinia';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import type { Message } from '@/features/agent/types';

/**
 * 消息处理器组合式函数
 * 负责过滤和处理消息，提供消息相关的方法
 *
 * @param {Object} params
 * @param {Ref<Array>} params.messages - 原始消息列表
 * @param {Ref<String>} params.userInput - 用户输入（用于建议选择）
 * @returns {Object} 包含可见消息列表和消息处理方法的对象
 */
export default function useMessageHandler({ messages, userInput }: { messages: Ref<Message[]>, userInput: Ref<string> }) {
  const agentStore = useAgentStore();
  const { deleteMessagesFrom } = agentStore;

  // --- Computed Properties ---

  /**
   * 过滤后的可见消息列表
   * 过滤掉所有 is_hidden 的消息，以及所有纯粹的系统/工具消息
   */
  const visibleMessages: ComputedRef<Message[]> = computed(() => {
    return messages.value.filter(m => {
      return !m.is_hidden && m.role !== 'system' && m.role !== 'tool';
    });
  });

  // --- Methods --

  /**
   * 处理建议选择事件
   * 将选中的建议文本添加到用户输入中
   *
   * @param {String} suggestionText - 建议文本
   */
  const handleSuggestionSelected = (suggestionText: string) => {
    if (userInput.value.trim() !== '') {
      userInput.value += '\n';
    }
    userInput.value += suggestionText;
  };

  /**
   * 处理建议发送事件
   * 直接发送建议文本作为消息
   *
   * @param {String} suggestionText - 建议文本
   */
  const handleSendSuggestionSelected = (suggestionText: string) => {
    // 这个方法在父组件中实现，因为需要访问 sendMessage 方法
    // 这里只是一个占位符，实际实现在父组件中
    console.log('handleSendSuggestionSelected:', suggestionText);
  };

  /**
   * 处理从某处删除消息事件
   * 删除指定消息及其之后的所有消息
   *
   * @param {String} messageId - 消息ID
   */
  const handleDeleteFrom = async (messageId: string) => {
    await deleteMessagesFrom(messageId);
  };

  /**
   * 处理重试事件
   * 重试最后一次对话
   */
  const handleRetry = () => {
    // 这个方法在父组件中实现，因为需要访问 retryLastTurn 方法
    // 这里只是一个占位符，实际实现在父组件中
    console.log('handleRetry');
  };

  return {
    visibleMessages,
    handleSuggestionSelected,
    handleSendSuggestionSelected,
    handleDeleteFrom,
    handleRetry
  };
}