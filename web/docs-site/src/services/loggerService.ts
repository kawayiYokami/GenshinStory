import { reactive, ref } from 'vue';
import type { Ref } from 'vue';

// --- 类型定义 ---
interface LogEntry {
  type: 'log' | 'error' | 'warn';
  timestamp: string;
  message: string;
  details: any[] | null;
}

// --- 响应式日志存储 ---
export const logs = reactive<LogEntry[]>([]);
export const lastRequest: Ref<any | null> = ref(null);

const logger = {
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

  clear(): void {
    logs.length = 0;
    lastRequest.value = null; // 同时清除请求
  },

  setLastRequest(requestBody: any): void {
    // 深拷贝以避免原始对象的响应性问题
    lastRequest.value = JSON.parse(JSON.stringify(requestBody));
  }
};

export default logger;