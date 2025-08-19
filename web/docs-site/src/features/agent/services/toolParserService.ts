import logger from '../../app/services/loggerService';
import localTools from './localToolsService';
import type { DocRequest } from './localToolsService';

// --- 类型定义 ---
interface ToolCallParams {
    [key: string]: string;
}

export interface ParsedToolCall {
    name: string;
    params: ToolCallParams;
    xml: string;
}

interface ParsedQuestion {
    xml: string;
    question: string;
    suggestions: string[];
}

const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs'];
const RETRYABLE_TOOLS = ['search_docs', 'read_doc', 'list_docs'];
let linkPromptContent: string | null = null;

async function _getLinkPrompt(): Promise<string> {
    if (linkPromptContent) {
        return linkPromptContent;
    }
    try {
        const v = Date.now();
        const response = await fetch(`/prompts/link_prompt.md?v=${v}`);
        if (!response.ok) {
            logger.error("无法加载 link_prompt.md");
            return "";
        }
        linkPromptContent = await response.text();
        return linkPromptContent;
    } catch (error) {
        logger.error("加载 link_prompt.md 时出错:", error);
        return "";
    }
}

/**
 * 从 API 的结构化 JSON 格式解析工具调用。
 */
function parseJsonToolCall(toolCall: any): ParsedToolCall | null {
    if (!toolCall || !toolCall.function) return null;
    
    const { name, arguments: args } = toolCall.function;

    if (!VALID_TOOLS.includes(name)) {
        logger.log(`[ToolParser] 解析到 JSON 工具调用 "<${name}>"，但它不在 VALID_TOOLS 白名单中。已忽略。`);
        return null;
    }

    try {
        const params = JSON.parse(args);
        return {
            name,
            params,
            xml: `<${name}>${JSON.stringify(params)}</${name}>`
        };
    } catch (error) {
        logger.error(`[ToolParser] 解析工具 '${name}' 的 JSON 参数时出错:`, error);
        return null;
    }
}

/**
 * 解析类 XML 字符串以查找工具调用。
 */
function parseXmlToolCall(xmlString: string): ParsedToolCall | null {
    if (typeof xmlString !== 'string') return null;

    const toolCallRegex = /<([a-zA-Z0-9_]+)>([\s\S]*?)<\/\1>/;
    const match = xmlString.match(toolCallRegex);

    if (!match) return null;

    const toolName = match[1];

    if (!VALID_TOOLS.includes(toolName)) {
        logger.log(`[ToolParser] 解析到 XML 标签 "<${toolName}>"，但它不在 VALID_TOOLS 白名单中。已忽略。`);
        return null;
    }

    const fullXml = match[0];
    const innerContent = match[2].trim();
    
    const params: ToolCallParams = {};
    const paramRegex = /<([a-zA-Z0-9_]+)>([\s\S]*?)<\/\1>/g;
    let paramMatch;
    
    while ((paramMatch = paramRegex.exec(innerContent)) !== null) {
        params[paramMatch[1]] = paramMatch[2].trim();
    }

    if (Object.keys(params).length === 0 && innerContent) {
        params.args = innerContent;
    }

    return { name: toolName, params, xml: fullXml };
}

/**
 * 解析 read_doc 工具调用的参数。
 */
function parseReadDocRequests(argsContent: string): DocRequest[] {
    const docRequests: DocRequest[] = [];
    if (argsContent && typeof argsContent === 'string') {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(`<root>${argsContent}</root>`, "text/xml");
        const docNodes = xmlDoc.querySelectorAll("doc");

        if (docNodes.length > 0) {
            docNodes.forEach(docNode => {
                const pathNode = docNode.querySelector("path");
                if (pathNode && pathNode.textContent) {
                    const request: DocRequest = { path: pathNode.textContent.trim(), lineRanges: [] };
                    const rangeNodes = docNode.querySelectorAll("line_range");
                    rangeNodes.forEach(rangeNode => {
                        if (rangeNode.textContent) {
                            request.lineRanges?.push(rangeNode.textContent.trim());
                        }
                    });
                    docRequests.push(request);
                }
            });
        } else {
            const pathNodes = xmlDoc.querySelectorAll("path");
            pathNodes.forEach(node => {
                if (node.textContent) {
                    docRequests.push({ path: node.textContent.trim(), lineRanges: [] });
                }
            });
        }
    }
    return docRequests;
}

/**
 * 为工具调用创建面向用户的状态消息。
 */
function createStatusMessage(parsedTool: ParsedToolCall): string {
    const { name, params } = parsedTool;
    switch (name) {
        case 'search_docs':
            return `正在搜索 "${params.query || params.regex || ''}" 的相关文档...`;
        case 'read_doc':
            return `正在读取文档...`;
        case 'list_docs':
            return `正在查看目录: \`${params.path || '/'}\`...`;
        default:
            return `正在执行工具: ${name}...`;
    }
}

/**
 * 执行工具并处理所有相关逻辑，如结果处理和错误处理。
 */
async function executeTool(parsedTool: ParsedToolCall): Promise<{ status: 'success' | 'error'; result: string; }> {
    const { name, params } = parsedTool;
    logger.log(`[ToolCoordinator] 准备执行工具: ${name}`, params);
    
    let toolResult: string;
    try {
        if (name === 'search_docs') {
            let query = params.query || params.regex || params.args;
            if (!query) throw new Error("查询工具收到了无效或缺失的查询参数。");
            toolResult = await localTools.searchDocs(query);
        } else if (name === 'read_doc') {
            const docRequests = parseReadDocRequests(params.args);
            if (docRequests.length === 0) {
                throw new Error("在 read_doc 调用中无效或缺失 path/doc 参数，或格式不正确。");
            }
            toolResult = await localTools.readDoc(docRequests);
        } else if (name === 'list_docs') {
            const path = params.path || '/';
            toolResult = await localTools.listDocs(path);
        } else {
            toolResult = `错误：未知的工具 '${name}'`;
            logger.error(`[ToolCoordinator] 尝试调用一个未知的工具: ${name}`);
        }
        
        // 在成功执行后，对于 list_docs 和 search_docs，附加 link_prompt
        if (['search_docs', 'list_docs'].includes(name) && toolResult && !toolResult.startsWith("错误：")) {
            const linkPrompt = await _getLinkPrompt();
            if (linkPrompt) {
                toolResult = `${toolResult}\n\n---\n\n${linkPrompt}`;
            }
        }
        
        // 返回成功状态和结果
        return { status: 'success', result: toolResult };
    } catch (e: any) {
        const errorMessage = `错误：执行工具 '${name}' 时发生异常: ${e.message}`;
        const errorDetails = e.stack ? `\n\n**详细错误日志:**\n\`\`\`\n${e.stack}\n\`\`\`` : '';
        const detailedErrorString = `${errorMessage}${errorDetails}`;
        logger.error(`[ToolCoordinator] 执行工具 '${name}' 异常:`, e);
        // 在发生错误时，返回错误状态和详细的错误信息
        return { status: 'error', result: detailedErrorString };
    }

    
}

/**
 * 从字符串中解析 <ask> UI 指令。
 */
function parseAskCall(xmlString: string): ParsedQuestion | null {
    if (typeof xmlString !== 'string') return null;

    const askRegex = /<ask>([\s\S]*?)<\/ask>/;
    const match = xmlString.match(askRegex);

    if (!match) return null;

    const fullXml = match[0];
    const innerContent = match[1].trim();
    
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(`<root>${innerContent}</root>`, "text/xml");

    const questionNode = xmlDoc.querySelector("question");
    const suggestNodes = xmlDoc.querySelectorAll("suggest");

    if (!questionNode || !questionNode.textContent) {
        logger.warn('[ToolParser] 解析到 <ask> 但内部没有找到有效的 <question> 标签。已忽略。');
        return null;
    }

    const suggestions = Array.from(suggestNodes).map(node => (node.textContent || '').trim());

    if (suggestions.length < 2 || suggestions.length > 10) {
        logger.warn(`[ToolParser] 解析到 <ask> 但找到了 ${suggestions.length} 个建议 (应为 2-4个)。已忽略。`);
        return null;
    }

    return {
        xml: fullXml,
        question: questionNode.textContent.trim(),
        suggestions: suggestions
    };
}

export function isToolRetryable(toolName: string): boolean {
    return RETRYABLE_TOOLS.includes(toolName);
}

export default {
    parseXmlToolCall,
    parseJsonToolCall,
    parseReadDocRequests,
    createStatusMessage,
    executeTool,
    parseAskCall,
    isToolRetryable,
};