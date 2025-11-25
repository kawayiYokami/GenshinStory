import logger from '@/features/app/services/loggerService';

/**
 * 将 Markdown 文本清洗为纯文本，以减少 token 使用
 * @param markdownText 原始 Markdown 文本
 * @returns 清洗后的纯文本
 */
export function stripMarkdown(markdownText: string): string {
    if (!markdownText) {
        return '';
    }

    try {
        let cleaned = markdownText;

        // 移除标题标记 (# ## ### 等)
        cleaned = cleaned.replace(/^#{1,6}\s+/gm, '');

        // 移除粗体标记 (**bold** 和 __bold__)
        // 先处理组合格式（粗斜体）
        cleaned = cleaned.replace(/\*\*\*(.*?)\*\*\*/g, '$1');
        cleaned = cleaned.replace(/\_\_\_(.*?)\_\_\_/g, '$1');

        // 移除粗体标记 (**bold** 和 __bold__)
        cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1');
        cleaned = cleaned.replace(/__(.*?)__/g, '$1');

        // 移除斜体标记 (*italic* 和 _italic_)
        cleaned = cleaned.replace(/\*([^\*]+?)\*/g, '$1');
        cleaned = cleaned.replace(/\b_([^_]+?)_\b/g, '$1');

        cleaned = cleaned.split('\n').map(line => line.trim()).join('\n');

        cleaned = cleaned.trim();

        return cleaned;
    } catch (error) {
        logger.error('清洗 Markdown 格式时出错:', error);
        return markdownText; // 出错时返回原文
    }
}

/**
 * 清洗 Markdown 但保留基本结构（标题、列表）
 * 用于需要一定可读性的场景
 * @param markdownText 原始 Markdown 文本
 * @returns 部分清洗后的文本
 */
export function lightenMarkdown(markdownText: string): string {
    if (!markdownText) {
        return '';
    }

    try {
        let cleaned = markdownText;

        // 只保留最影响 token 的格式

        // 移除粗体和斜体标记 - 按照与 stripMarkdown 相同的顺序和模式
        // 先处理组合格式（粗斜体）
        cleaned = cleaned.replace(/\*\*\*(.*?)\*\*\*/g, '$1');
        cleaned = cleaned.replace(/\_\_\_(.*?)\_\_\_/g, '$1');

        // 然后处理粗体标记
        cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1');
        cleaned = cleaned.replace(/__(.*?)__/g, '$1');

        // 最后处理斜体标记，使用改进的正则表达式避免在单词内匹配
        cleaned = cleaned.replace(/\*([^\*]+?)\*/g, '$1');
        cleaned = cleaned.replace(/\b_([^_]+?)_\b/g, '$1');

        // 移除行内代码
        cleaned = cleaned.replace(/`([^`]+)`/g, '$1');

        // 完全移除代码块
        cleaned = cleaned.replace(/```[\s\S]*?```/g, '');

        // 简化链接
        cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
        cleaned = cleaned.replace(/!\[([^\]]*)\]\([^)]+\)/g, '[图片]');
        cleaned = cleaned.replace(/\[\[([^\]|]+)(?:\|[^]]+)?\]\]/g, '$1');

        return cleaned;
    } catch (error) {
        logger.error('轻量化 Markdown 时出错:', error);
        return markdownText;
    }
}