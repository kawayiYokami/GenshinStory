/**
 * @fileoverview 会话管理服务模块
 * @description 负责管理聊天会话的创建、切换、删除等操作
 * @author yokami
 */
import { ref, type Ref } from 'vue';
import { nanoid } from 'nanoid';
import localforage from 'localforage';
import promptService from '../tools/implementations/promptService';
import logger from '@/features/app/services/loggerService';
import type { Session, AgentInfo } from '@/features/agent/types';

const MAX_SESSIONS_PER_DOMAIN = 10;

// --- SessionManager 类型定义 ---
/**
 * 会话管理器接口
 * @description 定义会话管理器的所有操作方法
 */
export interface SessionManager {
  /** 检查会话是否为空 */
  isSessionEmpty(session: Session | null): boolean;
  /** 切换到指定会话 */
  switchSession(sessionId: string, currentDomain: string | null): Promise<void>;
  /** 删除指定会话 */
  deleteSession(sessionId: string, currentDomain: string | null, startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>): void;
  /** 重命名会话 */
  renameSession(sessionId: string, newName: string): void;
  /** 开始新会话 */
  startNewSession(domain: string, roleIdToLoad: string | null, availableAgents: Ref<{ [key: string]: AgentInfo[] }>, activeRoleId: Ref<{ [key: string]: string | null }>, activeAgentName: Ref<string>, lastUsedRolesStore: LocalForage, sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): Promise<void>;
  /** 切换域上下文 */
  switchDomainContext(domain: string, fetchAvailableAgents: (domain: string) => Promise<string | null>, startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>, availableAgents: Ref<{ [key: string]: AgentInfo[] }>, activeRoleId: Ref<{ [key: string]: string | null }>, activeAgentName: Ref<string>, sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): Promise<void>;
  /** 使用指定代理开始新聊天 */
  startNewChatWithAgent(roleId: string, currentDomain: string | null, currentSession: Session | null, isLoading: Ref<boolean>, stop: () => void, fetchAvailableAgents: (domain: string) => Promise<string | null>, startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>, availableAgents: Ref<{ [key: string]: AgentInfo[] }>, activeRoleId: Ref<{ [key: string]: string | null }>, activeAgentName: Ref<string>, lastUsedRolesStore: LocalForage, sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): Promise<string | null>;
  /** 切换代理 */
  switchAgent(roleId: string, currentDomain: string | null, currentSession: Session | null, isLoading: Ref<boolean>, stop: () => void, fetchAvailableAgents: (domain: string) => Promise<string | null>, startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>, availableAgents: Ref<{ [key: string]: AgentInfo[] }>, activeRoleId: Ref<{ [key: string]: string | null }>, activeAgentName: Ref<string>, lastUsedRolesStore: LocalForage, sessions: Ref<{ [key: string]: Session }>, activeSessionIds: Ref<{ [key: string]: string | null }>): Promise<void>;
}

// --- SessionManager 实现 ---
/**
 * 会话管理器实现类
 * @description 实现会话管理器接口，提供具体的会话管理功能
 */
export class SessionManagerImpl implements SessionManager {
  private sessions: Ref<{ [key: string]: Session }>;
  private activeSessionIds: Ref<{ [key: string]: string | null }>;
  private activeRoleId: Ref<{ [key: string]: string | null }>;
  private activeAgentName: Ref<string>;
  private lastUsedRolesStore: LocalForage;
  private availableAgents: Ref<{ [key: string]: AgentInfo[] }>;

  /**
   * 构造函数
   * @description 初始化会话管理器，设置必要的引用
   * @param {Ref<{ [key: string]: Session }>} sessions 会话存储
   * @param {Ref<{ [key: string]: string | null }>} activeSessionIds 活跃会话ID存储
   * @param {Ref<{ [key: string]: string | null }>} activeRoleId 活跃角色ID存储
   * @param {Ref<string>} activeAgentName 活跃代理名称
   * @param {LocalForage} lastUsedRolesStore 最后使用角色存储
   * @param {Ref<{ [key: string]: AgentInfo[] }>} availableAgents 可用代理存储
   */
  constructor(
    sessions: Ref<{ [key: string]: Session }>,
    activeSessionIds: Ref<{ [key: string]: string | null }>,
    activeRoleId: Ref<{ [key: string]: string | null }>,
    activeAgentName: Ref<string>,
    lastUsedRolesStore: LocalForage,
    availableAgents: Ref<{ [key: string]: AgentInfo[] }>
  ) {
    this.sessions = sessions;
    this.activeSessionIds = activeSessionIds;
    this.activeRoleId = activeRoleId;
    this.activeAgentName = activeAgentName;
    this.lastUsedRolesStore = lastUsedRolesStore;
    this.availableAgents = availableAgents;
  }

  isSessionEmpty(session: Session | null): boolean {
    return !session || session.messageIds.length <= 1;
  }

  async switchSession(sessionId: string, currentDomain: string | null): Promise<void> {
    if (!currentDomain || !this.sessions.value[sessionId] || this.activeSessionIds.value[currentDomain] === sessionId) return;

    const targetSession = this.sessions.value[sessionId];
    const targetRoleId = targetSession.roleId;

    if (!targetRoleId) {
      logger.warn(`[SessionManager] 会话 ${sessionId} 没有 roleId。无法切换。`);
      return;
    }

    // 检查当前会话是否为空
    const currentSessionId = this.activeSessionIds.value[currentDomain];
    const currentSession = currentSessionId ? this.sessions.value[currentSessionId] : null;

    if (this.isSessionEmpty(currentSession) && currentSession && currentSessionId !== sessionId) {
      logger.log(`[SessionManager] 当前会话为空。正在转换到目标会话 ${sessionId}。`);

      // 转换逻辑：将当前空会话转换为目标会话
      currentSession.roleId = targetRoleId;
      currentSession.messagesById = { ...targetSession.messagesById };
      currentSession.messageIds = [...targetSession.messageIds];

      // 删除目标会话（因为已经转换到当前会话）
      delete this.sessions.value[sessionId];

      // 更新activeRoleId
      this.activeRoleId.value[currentDomain] = targetRoleId;
      await this.lastUsedRolesStore.setItem(currentDomain, targetRoleId);

      this.updateActiveAgentName(currentDomain);
      logger.log(`[SessionManager] 已将空会话 ${currentSessionId} 转换为会话 ${sessionId} (Agent: ${targetRoleId})。`);
    } else {
      // 正常切换逻辑
      this.activeSessionIds.value[currentDomain] = sessionId;
      this.activeRoleId.value[currentDomain] = targetRoleId;
      await this.lastUsedRolesStore.setItem(currentDomain, targetRoleId);

      this.updateActiveAgentName(currentDomain);
      logger.log(`[SessionManager] 已切换到会话 ${sessionId} (Agent: ${targetRoleId})。`);
    }
  }

  deleteSession(sessionId: string, currentDomain: string | null, startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>): void {
    if (!currentDomain || !this.sessions.value[sessionId]) return;

    if (this.activeSessionIds.value[currentDomain] === sessionId) {
      delete this.sessions.value[sessionId];
      logger.log(`[SessionManager] 已删除活动会话 ${sessionId}。正在开启一个新会话。`);
      startNewSession(currentDomain, this.activeRoleId.value[currentDomain]);
    } else {
      delete this.sessions.value[sessionId];
      logger.log(`[SessionManager] 已删除会话 ${sessionId}。`);
    }
  }

  renameSession(sessionId: string, newName: string): void {
    if (this.sessions.value[sessionId]) {
      this.sessions.value[sessionId].name = newName;
      logger.log(`[SessionManager] 已将会话 ${sessionId} 重命名为 "${newName}"`);
    }
  }

  updateActiveAgentName(currentDomain: string | null) {
    if (!currentDomain) return;
    const agent = this.availableAgents.value[currentDomain]?.find(a => a.id === this.activeRoleId.value[currentDomain]);
    if (agent) {
      this.activeAgentName.value = agent.name;
    }
  }

  async startNewSession(
    domain: string,
    roleIdToLoad: string | null,
    availableAgents: Ref<{ [key: string]: AgentInfo[] }>,
    activeRoleId: Ref<{ [key: string]: string | null }>,
    activeAgentName: Ref<string>,
    lastUsedRolesStore: LocalForage,
    sessions: Ref<{ [key: string]: Session }>,
    activeSessionIds: Ref<{ [key: string]: string | null }>
  ): Promise<void> {
    const roleId = roleIdToLoad || activeRoleId.value[domain];
    if (!roleId) {
      logger.error(`Agent Store: 无法开启新会话，因为没有提供或设置 roleId。`);
      // error.value = new Error("无法开启新会话，因为没有选择任何 Agent。");
      return;
    }
    logger.log(`Agent Store: 为域 '${domain}' (角色: ${roleId}) 开启新会话...`);

    const domainSessions = Object.values(sessions.value).filter(s => s.domain === domain);
    if (domainSessions.length >= MAX_SESSIONS_PER_DOMAIN) {
      domainSessions.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
      const oldestSession = domainSessions[0];
      logger.log(`Agent Store: 会话数量达到上限(${MAX_SESSIONS_PER_DOMAIN})，正在删除最旧的会话: ${oldestSession.id}`);
      delete sessions.value[oldestSession.id];
    }

    // isLoading.value = true;
    // error.value = null;
    try {
      const { systemPrompt, agentName } = await promptService.loadSystemPrompt(domain, roleId);
      activeAgentName.value = agentName;
      activeRoleId.value[domain] = roleId;
      const newSessionId = `session_${Date.now()}`;
      const newSession: Session = {
        id: newSessionId,
        domain: domain,
        roleId: roleId,
        name: `会话 ${new Date().toLocaleString()}`,
        createdAt: new Date().toISOString(),
        messagesById: {},
        messageIds: [],
      };

      sessions.value[newSessionId] = newSession;
      activeSessionIds.value[domain] = newSessionId;

      // Add system message - this will be done by the store
      // addMessage({
      //   role: 'system',
      //   content: systemPrompt,
      //   type: 'system',
      // });
      logger.log(`Agent Store: 新会话 '${newSessionId}' 已创建并激活。`);

    } catch (e: any) {
      // error.value = e;
      logger.error("Agent Store: 开启新会话失败:", e);
    } finally {
      // isLoading.value = false;
    }
  }

  async switchDomainContext(
    domain: string,
    fetchAvailableAgents: (domain: string) => Promise<string | null>,
    startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>,
    availableAgents: Ref<{ [key: string]: AgentInfo[] }>,
    activeRoleId: Ref<{ [key: string]: string | null }>,
    activeAgentName: Ref<string>,
    sessions: Ref<{ [key: string]: Session }>,
    activeSessionIds: Ref<{ [key: string]: string | null }>
  ): Promise<void> {
    logger.log(`Agent Store: 切换域上下文至 '${domain}'...`);
    const ensuredRoleId = await fetchAvailableAgents(domain);

    if (!activeSessionIds.value[domain] || !sessions.value[activeSessionIds.value[domain]]) {
      logger.log(`[AgentStore] '${domain}' 无活动会话。正在以角色 '${ensuredRoleId}' 开启新会话。`);
      await startNewSession(domain, ensuredRoleId);
    } else {
      const currentRole = availableAgents.value[domain]?.find(a => a.id === activeRoleId.value[domain]);
      if (currentRole) {
        activeAgentName.value = currentRole.name;
      }
      logger.log(`Agent Store: 已激活 '${domain}' 的现有会话 '${activeSessionIds.value[domain]}'。`);
    }
  }

  async startNewChatWithAgent(
    roleId: string,
    currentDomain: string | null,
    currentSession: Session | null,
    isLoading: Ref<boolean>,
    stop: () => void,
    fetchAvailableAgents: (domain: string) => Promise<string | null>,
    startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>,
    availableAgents: Ref<{ [key: string]: AgentInfo[] }>,
    activeRoleId: Ref<{ [key: string]: string | null }>,
    activeAgentName: Ref<string>,
    lastUsedRolesStore: LocalForage,
    sessions: Ref<{ [key: string]: Session }>,
    activeSessionIds: Ref<{ [key: string]: string | null }>
  ): Promise<string | null> {
    const domain = currentDomain;
    if (!domain || !roleId) return null;

    logger.log(`[AgentStore] 用户请求以 agent '${roleId}' 开始新聊天。`);

    const session = currentSession;
    const isSessionEmpty = !session || session.messageIds.length <= 1;

    if (isSessionEmpty && session) {
      logger.log(`[AgentStore] 当前会话为空。正在为新 agent 转换它。`);
      isLoading.value = true;
      stop();

      // 检查并修复流式完成状态，但永远不清空消息历史
      if (session.messageIds.length > 0) {
        for (const messageId of session.messageIds) {
          const message = session.messagesById[messageId];
          if (message && message.role === 'assistant') {
            // 修复 text 类型消息的 streamCompleted
            if (message.type === 'text') {
              const needsFix = (message.status === 'streaming' && message.streamCompleted !== true) ||
                              (message.status === 'error' && message.streamCompleted !== true);
              if (needsFix) {
                logger.log(`[SessionManager] 为助理消息 ${messageId} 设置 streamCompleted: true (原状态: ${message.status})`);
                message.streamCompleted = true;
              }
            }

            // 修复所有助理消息（包括 tool_status）的 status
            const needsStatusFix = message.status === 'streaming' || message.status === 'error' || message.status === 'rendering';
            if (needsStatusFix) {
              logger.log(`[SessionManager] 为助理消息 ${messageId} 更新 status: done (原状态: ${message.status})`);
              message.status = 'done';
            }
          }
        }
      }

      const { systemPrompt, agentName } = await promptService.loadSystemPrompt(domain, roleId);
      // 永远不清空消息历史，只更新agent信息
      session.roleId = roleId;
      activeRoleId.value[domain] = roleId;
      activeAgentName.value = agentName;
      await lastUsedRolesStore.setItem(domain, roleId);
      logger.log(`[AgentStore] 会话 ${session.id} 已为 agent ${roleId} 转换。`);
      isLoading.value = false;
      return systemPrompt;
    } else {
      logger.log(`[AgentStore] 当前会话不为空。正在开启一个新会话。`);
      await startNewSession(domain, roleId);
      return null;
    }
  }

  async switchAgent(
    roleId: string,
    currentDomain: string | null,
    currentSession: Session | null,
    isLoading: Ref<boolean>,
    stop: () => void,
    fetchAvailableAgents: (domain: string) => Promise<string | null>,
    startNewSession: (domain: string, roleIdToLoad: string | null) => Promise<void>,
    availableAgents: Ref<{ [key: string]: AgentInfo[] }>,
    activeRoleId: Ref<{ [key: string]: string | null }>,
    activeAgentName: Ref<string>,
    lastUsedRolesStore: LocalForage,
    sessions: Ref<{ [key: string]: Session }>,
    activeSessionIds: Ref<{ [key: string]: string | null }>
  ): Promise<void> {
    await this.startNewChatWithAgent(roleId, currentDomain, currentSession, isLoading, stop, fetchAvailableAgents, startNewSession, availableAgents, activeRoleId, activeAgentName, lastUsedRolesStore, sessions, activeSessionIds);
  }
}