import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import linkProcessorService from '@/lib/linkProcessor/linkProcessorService';
import type { LinkResolutionResult } from '@/lib/linkProcessor/linkProcessorService';

/**
 * 链接处理器组合式函数
 * 负责处理内部文档链接的点击事件，解析和打开链接
 *
 * @returns {Object} 包含链接处理方法的对象
 */
export default function useLinkProcessor() {
  /**
   * 处理链接点击事件
   * 检测点击的元素是否为内部文档链接，如果是则解析并打开链接
   *
   * @param {Event} event - 点击事件
   */
  const handleLinkClick = async (event: Event) => {
    const target = (event.target as HTMLElement).closest('.internal-doc-link') as HTMLElement | null;
    if (target && target.dataset.rawLink) {
      event.preventDefault();
      const rawLink = target.dataset.rawLink;
      const result: LinkResolutionResult = await linkProcessorService.resolveLink(rawLink);
      
      if (result.isValid && result.resolvedPath) {
        const docViewerStore = useDocumentViewerStore();
        docViewerStore.open(result.resolvedPath);
      } else {
        alert(`链接指向的路径 "${result.originalPath}" 无法被解析或找到。`);
      }
    }
  };

  return {
    handleLinkClick
  };
}