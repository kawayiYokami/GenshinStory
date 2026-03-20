import { defineStore } from 'pinia';
import { ref } from 'vue';
import localToolsService from '../../agent/tools/implementations/localToolsService';
import logger from '@/features/app/services/loggerService';
import { useAppStore } from '@/features/app/stores/app';
import filePathService from '@/features/app/services/filePathService';
import type { Ref } from 'vue';

export const useDocumentViewerStore = defineStore('documentViewer', () => {
  const appStore = useAppStore();
  const isVisible = ref(false);
  const isLoading = ref(false);
  const documentPath: Ref<string> = ref('');
  const documentContent: Ref<string> = ref('');
  const errorMessage: Ref<string> = ref('');
  const targetLine: Ref<number | null> = ref(null);
  const highlightKeywords: Ref<string[]> = ref([]);

  /**
   * 打开查看器并加载文档。
   * @param path 要打开的文档的逻辑路径。
   * @param lineNumber 可选，要跳转的行号。
   * @param keywords 可选，要高亮显示的关键词。
   */
  async function open(path: string, lineNumber?: number, keywords?: string[]): Promise<void> {
    const normalizedPath = filePathService.normalizeLogicalPath(path, {
      domain: appStore.currentDomain || undefined,
      ensureMdExtension: true,
    });
    logger.log(`[DocViewer] 正在打开文档: ${normalizedPath}${lineNumber ? ` (跳转到行 ${lineNumber})` : ''}`);
    isVisible.value = true;
    isLoading.value = true;
    documentPath.value = normalizedPath;
    targetLine.value = lineNumber || null;
    highlightKeywords.value = keywords || [];
    errorMessage.value = '';
    documentContent.value = ''; // 清除先前的内容

    try {
      const jsonResult = await localToolsService.readDoc([{ path: normalizedPath, preserveMarkdown: true }]);

      try {
        const parsedResult = JSON.parse(jsonResult);

        // 检查是否有文档数据
        if (parsedResult.docs && parsedResult.docs.length > 0) {
          const doc = parsedResult.docs[0];

          if (doc.error) {
            throw new Error(doc.error);
          }

          if (doc.content) {
            documentContent.value = doc.content;
          } else {
            throw new Error('文档内容为空');
          }
        } else {
          throw new Error('返回的 JSON 中没有找到文档数据');
        }
      } catch (e) {
        throw new Error(`从工具结果解析文档内容失败: ${(e as Error).message}`);
      }

    } catch (error: any) {
      logger.error(`[DocViewer] 加载文档 ${normalizedPath} 失败:`, error);
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
    targetLine.value = null;
    highlightKeywords.value = [];
  }

  /**
   * 设置目标行号（用于自动跳转）。
   * @param lineNumber 行号
   */
  function setTargetLine(lineNumber: number | null): void {
    targetLine.value = lineNumber;
  }

  return {
    isVisible,
    isLoading,
    documentPath,
    documentContent,
    errorMessage,
    targetLine,
    highlightKeywords,
    open,
    close,
    setTargetLine,
  };
});
