import { defineStore } from 'pinia';
import { ref } from 'vue';
import localToolsService from '@/services/localToolsService';
import logger from '@/services/loggerService';
import type { Ref } from 'vue';

export const useDocumentViewerStore = defineStore('documentViewer', () => {
  const isVisible = ref(false);
  const isLoading = ref(false);
  const documentPath: Ref<string> = ref('');
  const documentContent: Ref<string> = ref('');
  const errorMessage: Ref<string> = ref('');

  /**
   * 打开查看器并加载文档。
   * @param path 要打开的文档的逻辑路径。
   */
  async function open(path: string): Promise<void> {
    logger.log(`[DocViewer] 正在打开文档: ${path}`);
    isVisible.value = true;
    isLoading.value = true;
    documentPath.value = path;
    errorMessage.value = '';
    documentContent.value = ''; // 清除先前的内容

    try {
      const result = await localToolsService.readDoc(path);
      // readDoc 返回的结果是格式化的字符串，我们需要提取原始内容。
      const contentMatch = result.match(/--- DOC START:.*? ---\n\n([\s\S]*)\n\n--- DOC END:.*? ---/);
      
      if (contentMatch && contentMatch[1]) {
        documentContent.value = contentMatch[1];
      } else {
        // 处理 readDoc 返回错误消息字符串的情况
        throw new Error(`从工具结果解析文档内容失败: ${result}`);
      }

    } catch (error: any) {
      logger.error(`[DocViewer] 加载文档 ${path} 失败:`, error);
      errorMessage.value = `无法加载文档: ${error.message}`;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 关闭文档查看器。
   */
  function close(): void {
    isVisible.value = false;
    documentPath.value = '';
    documentContent.value = '';
    errorMessage.value = '';
  }

  return {
    isVisible,
    isLoading,
    documentPath,
    documentContent,
    errorMessage,
    open,
    close,
  };
});