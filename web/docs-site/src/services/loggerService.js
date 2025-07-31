import { reactive, ref } from 'vue';

// 创建一个响应式的日志存储
export const logs = reactive([]);
// 创建一个 ref 来存储最近的 API 请求
export const lastRequest = ref(null);

const logger = {
  log(message, ...details) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
      type: 'log',
      timestamp,
      message,
      details: details.length > 0 ? details : null,
    };
    logs.push(logEntry);
    console.log(message, ...details);
  },

  warn(message, ...details) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
      type: '.warn',
      timestamp,
      message,
      details: details.length > 0 ? details : null,
    };
    logs.push(logEntry);
    console.error(message, ...details);
  },

  error(message, ...details) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
      type: 'error',
      timestamp,
      message,
      details: details.length > 0 ? details : null,
    };
    logs.push(logEntry);
    console.error(message, ...details);
  },

  clear() {
    logs.length = 0;
    lastRequest.value = null; // Also clear the request on reset
  },

  setLastRequest(requestBody) {
    // Deep copy to avoid reactivity issues with the original object
    lastRequest.value = JSON.parse(JSON.stringify(requestBody));
  }
};

export default logger;