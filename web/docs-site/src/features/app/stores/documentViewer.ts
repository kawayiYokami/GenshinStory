import { defineStore } from 'pinia';
import { ref } from 'vue';
import localToolsService from '@/features/agent/services/localToolsService';
import logger from '@/features/app/services/loggerService';
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
      const xmlResult = await localToolsService.readDoc(path);
      
      try {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlResult, "text/xml");

        const parserError = xmlDoc.querySelector("parsererror");
        if (parserError) {
          throw new Error(`XML 解析错误: ${parserError.textContent}`);
        }

        const contentNode = xmlDoc.querySelector("doc > content");
        const errorNode = xmlDoc.querySelector("doc > error");

        if (contentNode) {
          documentContent.value = contentNode.textContent || '';
        } else if (errorNode) {
          throw new Error(errorNode.textContent || '发生未知错误');
        } else {
          throw new Error('在返回的 XML 中没有找到 <content> 或 <error> 标签。');
        }
      } catch (e) {
        throw new Error(`从工具结果解析文档内容失败: ${(e as Error).message}`);
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