import { defineStore } from 'pinia';
import { ref } from 'vue';
import localToolsService from '@/services/localToolsService';
import logger from '@/services/loggerService';

export const useDocumentViewerStore = defineStore('documentViewer', () => {
  const isVisible = ref(false);
  const isLoading = ref(false);
  const documentPath = ref('');
  const documentContent = ref('');
  const errorMessage = ref('');

  /**
   * Opens the viewer and loads a document.
   * @param {string} path - The logical path to the document to open.
   */
  async function open(path) {
    logger.log(`[DocViewer] Opening document: ${path}`);
    isVisible.value = true;
    isLoading.value = true;
    documentPath.value = path;
    errorMessage.value = '';
    documentContent.value = ''; // Clear previous content

    try {
      const result = await localToolsService.readDoc(path);
      // The result from readDoc is a formatted string, we need to extract the raw content.
      // Example: "--- DOC START: path ---\n\nCONTENT\n\n--- DOC END: path ---"
      const contentMatch = result.match(/--- DOC START:.*? ---\n\n([\s\S]*)\n\n--- DOC END:.*? ---/);
      
      if (contentMatch && contentMatch[1]) {
        documentContent.value = contentMatch[1];
      } else {
        // Handle cases where readDoc returns an error message string
        throw new Error(`Failed to parse document content from tool result: ${result}`);
      }

    } catch (error) {
      logger.error(`[DocViewer] Failed to load document ${path}:`, error);
      errorMessage.value = `无法加载文档: ${error.message}`;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Closes the document viewer.
   */
  function close() {
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