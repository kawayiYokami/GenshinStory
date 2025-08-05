import { marked } from 'marked';
import MarkdownPostprocessorService from '../services/MarkdownPostprocessorService';

self.onmessage = async (event) => {
    const { markdownText, originalId } = event.data;

    if (typeof markdownText !== 'string') {
        self.postMessage({
            html: '<p>错误：传入的 markdown 内容无效。</p>',
            originalId: originalId,
            error: '传入的 markdown 内容无效。'
        });
        return;
    }

    try {
        // 第一步：使用 marked.js 将 Markdown 转换为 HTML
        const rawHtml = await marked.parse(markdownText);
        
        // 第二步：后处理 HTML 以解析自定义链接
        const processedHtml = await MarkdownPostprocessorService.process(rawHtml);

        // 发送回处理过的 HTML
        self.postMessage({
            html: processedHtml,
            originalId: originalId
        });

    } catch (error: any) {
        console.error('Markdown Worker 中出错:', error);
        self.postMessage({
            html: `<p>渲染 Markdown 时出错: ${error.message}</p>`,
            originalId: originalId,
            error: error.message
        });
    }
};