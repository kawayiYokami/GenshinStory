/**
 * @fileoverview 日志服务模块
 * @description 提供应用程序的日志记录功能，支持多种日志级别和响应式日志存储
 * @author yokami
 */
import { reactive, ref } from 'vue';
import type { Ref } from 'vue';

// --- 类型定义 ---
/**
 * 日志条目接口
 * @description 定义日志条目的结构
 */
export interface LogEntry {
  /** 日志类型 */
  type: 'log' | 'error' | 'warn';
  /** 时间戳 */
  timestamp: string;
  /** 日志消息 */
  message: string;
  /** 详细信息 */
  details: any[] | null;
}

// --- 响应式日志存储 ---
/** 响应式日志存储数组 */
export const logs = reactive<LogEntry[]>([]);
/** 最后一次API请求的引用 */
export const lastRequest: Ref<any | null> = ref(null);

/**
 * 日志服务对象
 * @description 提供日志记录功能，包括普通日志、警告和错误日志
 */
const logger = {
  /**
   * 记录普通日志
   * @description 记录信息级别的日志，在开发环境同时输出到控制台
   * @param {string} message 日志消息
   * @param {...any} details 详细信息
   */
  log(message: string, ...details: any[]): void {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry: LogEntry = {
      type: 'log',
      timestamp,
      message,
      details: details.length > 0 ? details : null,
    };
    logs.push(logEntry);
    if (import.meta.env.DEV) {
      console.log(message, ...details);
    }
  },

  /**
   * 记录警告日志
   * @description 记录警告级别的日志，在开发环境同时输出到控制台
   * @param {string} message 警告消息
   * @param {...any} details 详细信息
   */
  warn(message: string, ...details: any[]): void {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry: LogEntry = {
      type: 'warn',
      timestamp,
      message,
      details: details.length > 0 ? details : null,
    };
    logs.push(logEntry);
    if (import.meta.env.DEV) {
      console.warn(message, ...details);
    }
  },

  /**
   * 记录错误日志
   * @description 记录错误级别的日志，在开发环境同时输出到控制台
   * @param {string} message 错误消息
   * @param {...any} details 详细信息
   */
  error(message: string, ...details: any[]): void {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry: LogEntry = {
      type: 'error',
      timestamp,
      message,
      details: details.length > 0 ? details : null,
    };
    logs.push(logEntry);
    if (import.meta.env.DEV) {
      console.error(message, ...details);
    }
  },

  /**
   * 清除所有日志
   * @description 清空日志存储和最后一次请求记录
   */
  clear(): void {
    logs.length = 0;
    lastRequest.value = null; // 同时清除请求
  },

  /**
   * 设置最后一次请求
   * @description 保存最后一次API请求的深拷贝副本
   * @param {any} requestBody 请求体内容
   */
  setLastRequest(requestBody: any): void {
    // 深拷贝以避免原始对象的响应性问题
    lastRequest.value = JSON.parse(JSON.stringify(requestBody));
  }
};

export default logger;