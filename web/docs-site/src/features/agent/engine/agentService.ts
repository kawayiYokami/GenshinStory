/**
 * @fileoverview 代理服务类
 * @description 智能代理系统的核心服务类，协调各个子服务完成对话流程
 * @author yokami
 *
 * 现代化重构：
 * - 移除 AgentToolService 依赖，工具执行由 SDK 自动管理
 */
import { type ComputedRef } from 'vue';
import type { Session } from '../types';
import type { MessageManager } from '../stores/messageManager';
import { AgentFlowService } from './AgentFlowService';
import { AgentContextService } from '../context/AgentContextService';
import { AgentApiService } from '../communication/AgentApiService';
import { AgentResponseHandlerService } from '../processing/responses/AgentResponseHandlerService';
import { agentCacheService } from '../state/AgentCacheService';

/**
 * 代理服务类
 * @description 负责协调各个子服务，提供统一的代理功能接口
 */
export class AgentService {
  private flowService: AgentFlowService;

  /**
   * 构造函数
   * @description 初始化代理服务，创建并配置各个子服务
   * @param {MessageManager} messageManager 消息管理器
   * @param {ComputedRef<Session | null>} currentSession 当前会话
   * @param {ComputedRef<any>} activeConfig 活跃配置
   */
  constructor(
    messageManager: MessageManager,
    currentSession: ComputedRef<Session | null>,
    activeConfig: ComputedRef<any>
  ) {
    const contextService = new AgentContextService(messageManager, currentSession, activeConfig);
    const apiService = new AgentApiService(messageManager, activeConfig);
    const responseHandlerService = new AgentResponseHandlerService(messageManager, currentSession);

    this.flowService = new AgentFlowService(
      messageManager,
      currentSession,
      contextService,
      apiService,
      null, // toolService 不再使用，保留参数兼容性
      responseHandlerService,
      activeConfig
    );
  }

  /**
   * 停止代理
   * @description 停止当前正在进行的代理处理流程
   * @return {Promise<void>} 停止完成的 Promise
   */
  public stopAgent(): Promise<void> {
    return this.flowService.stopAgent();
  }

  /**
   * 等待停止操作完成
   * @description 等待代理停止操作完成
   * @return {Promise<void>} 停止完成的 Promise
   */
  public waitForStop(): Promise<void> {
    return this.flowService.waitForStop();
  }

  /**
   * 开始新一轮对话
   * @description 启动代理的对话处理流程
   */
  public startTurn() {
    this.flowService.startTurn();
  }

  /**
   * 获取处理状态
   * @description 检查代理是否正在处理中
   * @return {boolean} 是否正在处理
   */
  public getIsProcessing(): boolean {
    return this.flowService.isProcessing.value;
  }

  /**
   * 获取连续AI轮次次数
   * @description 获取连续的AI对话轮次次数
   * @return {number} 连续AI轮次次数
   */
  public getConsecutiveAiTurns(): number {
    return this.flowService.consecutiveAiTurns.value;
  }

  /**
   * 强制清除代理缓存
   * @description 清除所有代理相关的缓存数据
   * @return {Promise<void>}
   * @throws {Error} 当清除缓存失败时抛出异常
   */
  public static async forceClearAgentCache(): Promise<void> {
    await agentCacheService.forceClearAgentCache();
  }
}