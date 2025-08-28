
import logger from '../../app/services/loggerService';
import { toolPromptService } from './toolPromptService';
import { toolRegistryService } from '../tools/toolRegistryService';
import { toolStateService } from '../tools/toolStateService';
import type { DocRequest } from './localToolsService';
import parserAdapter, { type ParsedToolCall as AdapterParsedToolCall } from './parserAdapter';

// --- 类型定义 ---
interface ToolCallParams {
    [key: string]: string | object | any;
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

const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs', 'ask'];
const RETRYABLE_TOOLS = ['search_docs', 'read_doc', 'list_docs'];
let linkPromptContent: string | null = null;

/**
 * 智能转换工具参数
 */
function convertParams(toolName: string, params: Record<string, any>): ToolCallParams {
    const converted: ToolCallParams = {};

    switch (toolName) {
        case 'read_doc':
            // read_doc 工具只保留 args 参数的对象结构
            for (const [key, value] of Object.entries(params)) {
                if (key === 'args' && typeof value === 'object' && value !== null) {
                    // 对于 args 参数，如果是对象则保留
                    converted[key] = value;
                } else if (typeof value === 'object' && value !== null) {
                    // 其他对象参数转换为 JSON 字符串
                    converted[key] = JSON.stringify(value);
                } else if (value === null || value === undefined) {
                    // 处理 null 和 undefined
                    converted[key] = String(value);
                } else {
                    converted[key] = value;
                }
            }
            break;

        case 'search_docs':
        case 'list_docs':
        case 'ask':
        default:
            // 其他工具保持原有逻辑
            for (const [key, value] of Object.entries(params)) {
                if (typeof value === 'string') {
                    converted[key] = value;
                } else {
                    converted[key] = JSON.stringify(value);
                }
            }
            break;
    }

    return converted;
}

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
    // 使用 parserAdapter 解析 JSON 工具调用
    const result = parserAdapter.parseJsonToolCall(toolCall);
    if (!result) return null;

    // 智能转换参数类型
    const params = convertParams(result.name, result.params);

    return {
        name: result.name,
        params,
        xml: result.xml
    };
}

/**
 * 解析类 XML 字符串以查找工具调用。
 */
function parseXmlToolCall(xmlString: string): ParsedToolCall | null {
    if (typeof xmlString !== 'string') return null;

    // 使用 parserAdapter 解析 XML
    const result = parserAdapter.parseSingleToolCall(xmlString);
    if (!result) return null;

    // 智能转换参数类型
    const params = convertParams(result.name, result.params);

    return {
        name: result.name,
        params,
        xml: result.xml
    };
}

/**
 * 解析 read_doc 工具调用的参数。
 */
function parseReadDocRequests(argsContent: string): DocRequest[] {
    if (!argsContent || typeof argsContent !== 'string') {
        return [];
    }

    // 使用 parserAdapter 解析 read_doc 请求
    const requests = parserAdapter.parseReadDocRequests(argsContent);

    // 转换格式以兼容旧接口
    return requests.map(request => ({
        path: request.path,
        lineRanges: request.lineRanges || []
    }));
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
        case 'ask':
            return `正在向用户提问...`;
        default:
            return `正在执行工具: ${name}...`;
    }
}

/**
 * 执行工具并处理所有相关逻辑，如结果处理和错误处理。
 */
async function executeTool(parsedTool: ParsedToolCall): Promise<{ status: 'success' | 'error'; result: string; followUpPrompt?: string }> {
    const { name, params } = parsedTool;
    logger.log(`[ToolCoordinator] 准备执行工具: ${name}`, params);

    try {
        // 从工具注册表获取工具实例
        const tool = toolRegistryService.getTool(name);
        if (!tool) {
            const errorMessage = `错误：未知的工具 '${name}'`;
            logger.error(`[ToolCoordinator] 尝试调用一个未知的工具: ${name}`);
            return { status: 'error', result: errorMessage };
        }

        // 根据工具类型决定执行逻辑
        let executionResult;

        if (tool.type === 'ui') {
            // UI工具不执行后端逻辑，直接返回空结果
            executionResult = { result: '' };
        } else {
            // 执行工具
            executionResult = await tool.execute(params);
        }

        let finalResult = executionResult.result;

        // 对于执行工具，处理后续提示逻辑
        if (tool.type === 'execution') {
            // 获取所有应在当前工具执行后作为后续提示提供的工具
            const followUpTools = toolRegistryService.getFollowUpTools(name);

            // 遍历后续工具，检查状态并追加提示
            for (const followUpTool of followUpTools) {
                if (!toolStateService.hasPromptBeenSent(followUpTool.name)) {
                    // 格式化后续工具提示
                    const followUpPrompt = formatFollowUpPrompt(followUpTool);
                    finalResult += `\n\n---\n\n${followUpPrompt}`;

                    // 标记提示为已发送
                    toolStateService.markPromptAsSent(followUpTool.name);
                }
            }

            // 对于 list_docs 和 search_docs，附加 link_prompt（保持向后兼容）
            if (['search_docs', 'list_docs'].includes(name) && finalResult && !finalResult.startsWith("错误：")) {
                const linkPrompt = await _getLinkPrompt();
                if (linkPrompt) {
                    finalResult = `${finalResult}\n\n---\n\n${linkPrompt}`;
                }
            }
        }

        // 返回成功状态、结果和后续提示
        // 重置当前工具的提示状态，以便下次调用时可以重新显示提示
        toolStateService.resetToolPromptState(name);

        return {
            status: 'success',
            result: finalResult,
            followUpPrompt: executionResult.followUpPrompt
        };
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
 * 格式化后续工具提示
 */
function formatFollowUpPrompt(tool: any): string {
    let prompt = `**下一步操作建议**\n`;
    prompt += `您可以使用 ${tool.name} 工具来：${tool.description}\n\n`;
    prompt += `**使用方法:**\n${tool.usage}\n\n`;

    if (tool.examples && tool.examples.length > 0) {
        prompt += `**示例:**\n`;
        tool.examples.forEach((example: string) => {
            prompt += `- ${example}\n`;
        });
    }

    return prompt;
}

/**
 * 从字符串中解析 <ask> UI 指令。
 */
function parseAskCall(xmlString: string): ParsedQuestion | null {
    if (typeof xmlString !== 'string') return null;

    // 使用 parserAdapter 解析 ask 调用
    const result = parserAdapter.parseAskCall(xmlString);
    if (!result) return null;

    return {
        xml: result.xml,
        question: result.question,
        suggestions: result.suggestions
    };
}

export function isToolRetryable(toolName: string): boolean {
    return RETRYABLE_TOOLS.includes(toolName);
}

export { convertParams };

export default {
    parseXmlToolCall,
    parseJsonToolCall,
    parseReadDocRequests,
    createStatusMessage,
    executeTool,
    parseAskCall,
    isToolRetryable,
};

export { parseReadDocRequests };