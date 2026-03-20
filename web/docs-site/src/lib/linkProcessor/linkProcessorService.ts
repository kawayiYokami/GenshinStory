import pathService from '../../features/app/services/pathService';
import { useAppStore } from '@/features/app/stores/app';
import filePathService from '@/features/app/services/filePathService';

// --- 类型定义 ---
export interface LinkResolutionResult {
  isValid: boolean;
  displayText: string;
  originalPath: string;
  resolvedPath: string | null;
  rawLink: string;
  lineNumber?: number;
}

class LinkProcessorService {
  /**
   * 解析原始的 wiki 风格链接，解析其路径，并返回一个结构化对象。
   * 这是处理内联链接的唯一真实来源。
   * @param rawLinkText 原始链接文本, 例如 "[[显示文本|path:some/path.md]]"。
   * @returns 一个包含解析结果的对象。
   */
  public async resolveLink(rawLinkText: string): Promise<LinkResolutionResult> {
    const baseResult: LinkResolutionResult = {
      isValid: false,
      displayText: rawLinkText,
      originalPath: rawLinkText,
      resolvedPath: null,
      rawLink: rawLinkText
    };

    if (typeof rawLinkText !== 'string') {
      return baseResult;
    }

    // 增强的正则表达式以处理官方和原始格式，支持行号
    const genericLinkRegex = /\[\[([^|\]]+)(?:\|path:([^\]]+))?(?:\|([^\]]+))?\]\]/;
    const match = rawLinkText.match(genericLinkRegex);

    if (!match) {
        return baseResult;
    }

    const group1 = match[1]; // 始终是显示文本或完整路径
    const group2 = match[2]; // 来自 "path:" 语法的路径
    const group3 = match[3]; // 来自原始语法的路径

    const displayText = group1.trim();
    // 路径可能在 group2 (官方格式), group3 (原始格式), 或 group1 (仅路径格式)
    let originalPath = (group2 || group3 || group1).trim();

    // 提取行号（如果存在）：只解析路径末尾的 :number 或 :start-end
    let lineNumber: number | undefined;
    const lineMatch = originalPath.match(/^(.*):(\d+(?:-\d+)?)$/);
    if (lineMatch) {
      originalPath = lineMatch[1].trim();
      const firstLine = lineMatch[2].split('-')[0];
      if (/^\d+$/.test(firstLine)) {
        lineNumber = parseInt(firstLine, 10);
      }
    }

    const appStore = useAppStore();
    originalPath = filePathService.normalizeLogicalPath(originalPath, {
      domain: appStore.currentDomain || undefined,
      ensureMdExtension: false,
    });

    baseResult.displayText = displayText;
    baseResult.originalPath = originalPath;
    baseResult.lineNumber = lineNumber;

    try {
      const resolvedPath = await pathService.resolveLogicalPath(originalPath);
      
      if (resolvedPath) {
        return {
          ...baseResult,
          isValid: true,
          resolvedPath
        };
      } else {
        return {
          ...baseResult,
          isValid: false,
        };
      }
    } catch (error) {
      return {
        ...baseResult,
        isValid: false,
      };
    }
  }
}

const linkProcessorService = new LinkProcessorService();
export default linkProcessorService;
