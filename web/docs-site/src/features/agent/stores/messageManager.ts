import { nanoid } from 'nanoid';
import { nextTick } from 'vue';
import logger from '@/features/app/services/loggerService';
import type { Message, Session } from '../types';

// --- MessageManager 类型定义 ---
export interface MessageManager {
  addMessage(messageData: Partial<Message>): Promise<Message | null>;
  updateMessage({ messageId, updates }: { messageId: string, updates: Partial<Message> }): Promise<void>;
  removeMessage(messageId: string): Promise<void>;
  replaceMessage(oldId: string, newMessageData: Partial<Message>): Promise<void>;
  appendMessageContent({ messageId, chunk }: { messageId: string, chunk: string }): Promise<void>;
  markStreamAsCompleted({ messageId }: { messageId: string }): void;
}

// --- MessageManager 实现 ---
export class MessageManagerImpl implements MessageManager {
  private currentSession: Session | null;

  constructor(currentSession: Session | null) {
    this.currentSession = currentSession;
  }

  setCurrentSession(session: Session | null) {
    this.currentSession = session;
  }

  async addMessage(messageData: Partial<Message>): Promise<Message | null> {
    if (!this.currentSession) return null;

    const id = messageData.id || nanoid();
    const message: Message = {
      id,
      type: 'text',
      role: 'user', // default role
      randomSeed: Math.floor(Math.random() * 1000000), // 生成随机种子，用于确定性选择表情图片
      ...messageData,
    } as Message;

    this.currentSession.messagesById[id] = message;
    this.currentSession.messageIds.push(id);
    await nextTick();
    return message;
  }

  async updateMessage({ messageId, updates }: { messageId: string, updates: Partial<Message> }): Promise<void> {
    const session = this.currentSession;
    if (!session) return;

    const message = session.messagesById[messageId];
    if (message) {
      session.messagesById[messageId] = {
        ...message,
        ...updates,
      };
      await nextTick();
    }
  }

  async removeMessage(messageId: string): Promise<void> {
    const session = this.currentSession;
    if (!session || !session.messagesById[messageId]) return;

    const index = session.messageIds.indexOf(messageId);
    if (index > -1) {
      session.messageIds.splice(index, 1);
    }
    delete session.messagesById[messageId];
    await nextTick();
  }

  async replaceMessage(oldId: string, newMessageData: Partial<Message>): Promise<void> {
    logger.log(`[LOG] agentStore: Replacing message ${oldId}`, { newMessageData });
    const session = this.currentSession;
    if (!session || !session.messagesById[oldId]) return;

    const index = session.messageIds.indexOf(oldId);
    if (index === -1) return;

    const newId = newMessageData.id || nanoid();

    // 先设置默认值，再用传入数据覆盖（与 addMessage 保持一致）
    const message: Message = {
      id: newId,
      role: 'assistant',
      type: 'text',
      content: '',
      createdAt: new Date().toISOString(),
      randomSeed: Math.floor(Math.random() * 1000000),
      ...newMessageData,
    } as Message;

    delete session.messagesById[oldId];
    session.messagesById[newId] = message;

    session.messageIds.splice(index, 1, newId);
    await nextTick();
  }

  async appendMessageContent({ messageId, chunk }: { messageId: string, chunk: string }): Promise<void> {
    const session = this.currentSession;
    if (!session) return;

    const message = session.messagesById[messageId];
    if (message) {
        const oldContent = message.content;
        const newContent = (Array.isArray(oldContent) ? oldContent.map(c=>c.text).join('') : (oldContent || '')) + chunk;
        session.messagesById[messageId] = {
            ...message,
            content: newContent,
        };
        await nextTick();
    }
  }

  markStreamAsCompleted({ messageId }: { messageId: string }): void {
    const message = this.currentSession?.messagesById?.[messageId];
    if (message) {
      message.streamCompleted = true;
    }
  }
}

export default MessageManagerImpl;