import tokenizerService from '@/lib/tokenizer/tokenizerService';
import yaml from 'js-yaml';
import logger from '../../../app/services/loggerService';
import { useConfigStore } from '@/features/app/stores/config';
import { storeToRefs } from 'pinia';
import type { Message, MessageContentPart } from '@/features/agent/stores/agentStore';
import llmProviderService from '@/lib/llm/llmProviderService';
import type { CoreMessage } from 'ai';

// --- 类型定义 ---

interface PaperGenerationResult {
    success: boolean;
    paperContent?: string;
    error?: string;
}

interface PromptTemplate {
    final_prompt_structure: string;
    role_definition: string;
    content_structure_guide: string;
    [key: string]: any;
}

/**
 * 游戏知识报告生成服务
 * 基于技术对话记录生成适合发布在知乎、游戏攻略站的知识分析文章
 */
class AcademicPaperGeneratorService {
    private promptTemplate: PromptTemplate | null = null;

    /**
     * 加载论文生成提示词模板
     */
    private async loadPromptTemplate(): Promise<PromptTemplate> {
        if (this.promptTemplate) {
            return this.promptTemplate;
        }

        try {
            const response = await fetch('/prompts/optimizers/academic_paper_generator_prompt.yaml');
            if (!response.ok) {
                throw new Error(`Failed to load prompt template: ${response.statusText}`);
            }
            const yamlText = await response.text();
            this.promptTemplate = yaml.load(yamlText) as PromptTemplate;
            return this.promptTemplate;
        } catch (error) {
            logger.error('[论文生成器] 加载提示词模板失败:', error);
            throw new Error('无法加载论文生成提示词模板');
        }
    }

    /**
     * 主公共入口点，基于对话记录生成知识分析报告
     * @param messages 完整的当前消息历史记录
     * @returns 包含生成状态和结果的对象
     */
    public async generateAcademicPaper(messages: Message[]): Promise<PaperGenerationResult> {
        logger.log('[知识报告生成器] 开始生成知识分析报告...');

        try {
            // 1. 加载提示词模板
            const promptTemplate = await this.loadPromptTemplate();

            // 2. 提取对话内容
            const dialogueBlock = this.extractDialogueContent(messages);

            // 3. 构建完整提示词
            const finalPrompt = promptTemplate.final_prompt_structure
                .replace('{dialogue_block}', dialogueBlock)
                .replace('{content_structure_guide}', promptTemplate.content_structure_guide);

            // 4. 调用AI服务生成报告
            const paperContent = await this.callAIService(finalPrompt);

            return { success: true, paperContent };
        } catch (error) {
            logger.error('[知识报告生成器] 生成报告失败:', error);
            const errorMessage = error instanceof Error ? error.message : '生成知识报告失败，请稍后重试';
            return { success: false, error: errorMessage };
        }
    }

    /**
     * 从消息中提取对话内容
     * @param messages 消息列表
     * @returns 格式化的对话文本
     */
    private extractDialogueContent(messages: Message[]): string {
        // 过滤掉系统消息、工具调用和压缩摘要，只保留用户和助手的对话
        const relevantMessages = messages.filter(msg =>
            msg.role === 'user' ||
            (msg.role === 'assistant' && typeof msg.content === 'string' &&
             !msg.content?.includes('tool_results') &&
             !msg.content?.includes('search_docs') &&
             !msg.content?.includes('[') // 过滤掉系统消息格式
            )
        );

        // 构建对话文本
        const dialogue = relevantMessages.map(msg => {
            const role = msg.role === 'user' ? '用户' : '助手';
            const content = this.extractTextFromContent(msg.content);
            return `${role}: ${content}`;
        }).join('\n\n');

        return dialogue;
    }

    /**
     * 从消息内容中提取文本
     * @param content 消息内容
     * @returns 提取的文本
     */
    private extractTextFromContent(content: string | MessageContentPart[]): string {
        if (typeof content === 'string') {
            return content || '';
        }

        if (Array.isArray(content)) {
            return content
                .filter(part => part.type === 'text' && part.text)
                .map(part => part.text || '')
                .join(' ');
        }

        return '';
    }

    /**
     * 调用AI服务生成论文
     * @param prompt 完整的提示词
     * @returns 生成的论文内容
     */
    private async callAIService(prompt: string): Promise<string> {
        const configStore = useConfigStore();
        const { activeConfig } = storeToRefs(configStore);

        if (!activeConfig.value) {
            throw new Error('未配置有效的AI服务');
        }

        try {
            const messages: CoreMessage[] = [
                {
                    role: 'system',
                    content: '你是一个专业的游戏知识分析专家，擅长将技术对话转化为高质量的知识分析文章。请严格按照指定的结构要求和内容真实性原则生成内容。'
                },
                { role: 'user', content: prompt }
            ];

            const response = await llmProviderService.createChatCompletion(
                messages,
                activeConfig.value,
                new AbortController().signal
            );

            // 提取响应内容（Vercel AI SDK 格式）
            if (response.text) {
                return response.text;
            } else if (response.choices && response.choices[0]?.message?.content) {
                return response.choices[0].message.content;
            } else {
                throw new Error('AI服务返回了无效的响应格式');
            }
        } catch (error) {
            logger.error('[论文生成器] AI服务调用失败:', error);
            throw new Error(`AI服务调用失败: ${error instanceof Error ? error.message : '未知错误'}`);
        }
    }

    /**
     * 下载论文为Markdown文件或PDF文件
     * @param paperContent 论文内容
     * @param format 下载格式，'md' 或 'pdf'
     */
    downloadPaper(paperContent: string, format: 'md' | 'pdf' = 'md'): void {
        try {
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');

            if (format === 'md') {
                // Markdown 下载逻辑
                const filename = `knowledge-report-${timestamp}.md`;
                const blob = new Blob([paperContent], { type: 'text/markdown;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                logger.log('[论文生成器] Markdown 论文下载成功:', filename);
            } else if (format === 'pdf') {
                // PDF 下载逻辑 - 使用原生打印
                this.downloadAsPDF(paperContent, timestamp);
            }
        } catch (error) {
            logger.error('[论文生成器] 下载失败:', error);
            throw new Error('下载论文失败');
        }
    }

    /**
     * 将Markdown内容转换为PDF并下载
     * @param markdownContent Markdown内容
     * @param timestamp 时间戳
     */
    private downloadAsPDF(markdownContent: string, timestamp: string): void {
        // 创建一个隐藏的iframe用于打印
        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = 'none';
        iframe.style.visibility = 'hidden';

        document.body.appendChild(iframe);

        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
        if (!iframeDoc) {
            document.body.removeChild(iframe);
            throw new Error('无法创建打印文档');
        }

        // 简单的Markdown到HTML转换
        const htmlContent = this.markdownToHTML(markdownContent);

        // 写入HTML内容
        iframeDoc.open();
        iframeDoc.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>知识报告</title>
                <meta charset="utf-8">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        color: #333;
                    }
                    h1, h2, h3, h4, h5, h6 {
                        color: #2c3e50;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }
                    h1 { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                    h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 8px; }
                    h3 { font-size: 1.25em; }
                    p { margin-bottom: 1em; }
                    ul, ol { margin-left: 20px; margin-bottom: 1em; }
                    li { margin-bottom: 0.5em; }
                    blockquote {
                        border-left: 4px solid #ddd;
                        margin: 0;
                        padding-left: 20px;
                        color: #666;
                        font-style: italic;
                    }
                    code {
                        background-color: #f4f4f4;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Monaco', 'Consolas', monospace;
                    }
                    pre {
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                        margin: 1em 0;
                    }
                    pre code {
                        background-color: transparent;
                        padding: 0;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin: 1em 0;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: left;
                    }
                    th { background-color: #f5f5f5; font-weight: bold; }
                    em { font-style: italic; }
                    strong { font-weight: bold; }
                    @media print {
                        body { margin: 0; padding: 15px; }
                        h1 { page-break-after: avoid; }
                        h2, h3 { page-break-after: avoid; }
                        pre, blockquote { page-break-inside: avoid; }
                    }
                </style>
            </head>
            <body>
                ${htmlContent}
            </body>
            </html>
        `);
        iframeDoc.close();

        // 等待内容加载完成后触发打印
        setTimeout(() => {
            iframe.contentWindow?.print();

            // 打印对话框关闭后移除iframe
            setTimeout(() => {
                document.body.removeChild(iframe);
            }, 1000);
        }, 500);

        logger.log('[论文生成器] PDF 下载已触发');
    }

    /**
     * 简单的Markdown到HTML转换
     * @param markdown Markdown文本
     * @returns HTML字符串
     */
    private markdownToHTML(markdown: string): string {
        return markdown
            // 标题
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // 粗体和斜体
            .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // 代码块
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            // 引用
            .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
            // 无序列表
            .replace(/^\* (.+)$/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // 有序列表
            .replace(/^\d+\. (.+)$/gim, '<li>$1</li>')
            // 段落
            .replace(/\n\n/g, '</p><p>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>')
            // 清理多余的标签
            .replace(/<p><h([1-6])>/g, '<h$1>')
            .replace(/<\/h([1-6])><\/p>/g, '</h$1>')
            .replace(/<p><ul>/g, '<ul>')
            .replace(/<\/ul><\/p>/g, '</ul>')
            .replace(/<p><blockquote>/g, '<blockquote>')
            .replace(/<\/blockquote><\/p>/g, '</blockquote>')
            .replace(/<p><pre>/g, '<pre>')
            .replace(/<\/pre><\/p>/g, '</pre>');
    }

    /**
     * 检查是否有足够的对话内容生成论文
     * @param messages 消息列表
     * @returns 是否可以生成论文
     */
    canGeneratePaper(messages: Message[]): boolean {
        // 需要至少6条消息才能生成有意义的论文
        const relevantMessages = messages.filter(msg =>
            msg.role === 'user' ||
            (msg.role === 'assistant' && typeof msg.content === 'string' &&
             !msg.content?.includes('tool_results') &&
             !msg.content?.includes('search_docs'))
        );

        return relevantMessages.length >= 6;
    }
}

// 导出单例实例
export const academicPaperGeneratorService = new AcademicPaperGeneratorService();