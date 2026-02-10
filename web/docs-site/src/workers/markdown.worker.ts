import { renderMarkdownSync, replaceLinkPlaceholders } from "../features/viewer/services/MarkdownRenderingService";

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
        // 第一步：使用新的同步渲染函数将 Markdown 转换为带有占位符的 HTML
        const htmlWithPlaceholders = renderMarkdownSync(markdownText);
        
        // 第二步：异步替换占位符为最终的链接
        const finalHtml = await replaceLinkPlaceholders(htmlWithPlaceholders);

        // 发送回处理过的 HTML
        self.postMessage({
            html: finalHtml,
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