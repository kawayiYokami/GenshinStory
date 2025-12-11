
import logger from '../../app/services/loggerService';
import { toolPromptService } from './toolPromptService';
import { toolRegistryService } from '../tools/toolRegistryService';
import type { DocRequest } from './localToolsService';
import jsonParserService from './JsonParserService';
import { FlatToolCall, NestedToolCall, isFlatToolCall, convertToFlatToolCall } from '../types';

// --- 类型定义 ---
interface ToolCallParams {
    [key: string]: string | object | any;
}

export interface ParsedToolCall {
    name: string;
    params: ToolCallParams;
    /** 原始的工具调用字符串（JSON格式） */
    original: string;
}

interface ParsedQuestion {
    /** 原始的 ask_choice 调用字符串（JSON格式） */
    original: string;
    question: string;
    suggestions: string[];
}

const VALID_TOOLS = ['search_docs', 'read_doc', 'ask_choice'];
let linkPromptContent: string | null = null;

/**
 * 智能转换工具参数（支持平铺和嵌套格式）
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

        case 'ask_choice':
            // ask_choice 工具的 suggestions 字段统一处理为平铺格式
            for (const [key, value] of Object.entries(params)) {
                if (key === 'suggestions' && Array.isArray(value)) {
                    // 平铺格式的suggestions字段保持数组不变
                    converted[key] = value;
                } else if (typeof value === 'string') {
                    converted[key] = value;
                } else {
                    converted[key] = JSON.stringify(value);
                }
            }
            break;

        case 'search_docs':
            // search_docs 工具特殊处理，确保 maxResults 参数保持数字类型
            for (const [key, value] of Object.entries(params)) {
                if (key === 'maxResults' && typeof value === 'number') {
                    // 保持 maxResults 为数字类型
                    converted[key] = value;
                } else if (typeof value === 'string') {
                    converted[key] = value;
                } else {
                    converted[key] = JSON.stringify(value);
                }
            }
            break;
        default:
            // 其他工具保持原有逻辑，支持 doc_path 参数
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
 * 解析工具调用字符串（使用JsonParserService统一处理）
 */
function parseToolCall(input: string | Record<string, any>): ParsedToolCall | null {
    let parsedResult: any;

    if (typeof input === 'string') {
        // 使用 JsonParserService 直接解析
        const result = jsonParserService.parseLlmResponse(input);
        parsedResult = result ? result.toolCall : null;
    } else if (typeof input === 'object' && input !== null) {
        // 直接处理对象格式
        parsedResult = input;
    } else {
        return null;
    }

    if (!parsedResult || !parsedResult.tool) {
        return null;
    }

    // 转换为 ParsedToolCall 格式
    const params: ToolCallParams = {};

    // 根据工具类型提取参数
    switch (parsedResult.tool) {
        case 'search_docs':
            if (parsedResult.query) params.query = parsedResult.query;
            if (parsedResult.path) params.path = parsedResult.path;
            if (parsedResult.limit) params.limit = parsedResult.limit;
            if (parsedResult.maxResults) params.maxResults = parsedResult.maxResults;
            break;
        case 'read_doc':
            if (parsedResult.path) params.path = parsedResult.path;
            if (parsedResult.target) params.target = parsedResult.target;
            if (parsedResult.line_range) params.line_range = parsedResult.line_range;
            break;
        case 'ask_choice':
            if (parsedResult.question) params.question = parsedResult.question;
            if (parsedResult.suggestions) params.suggestions = parsedResult.suggestions;
            break;
    }

    return {
        name: parsedResult.tool,
        params: convertParams(parsedResult.tool, params),
        original: typeof input === 'string' ? input : JSON.stringify(input)
    };
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
        case 'ask_choice':
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

        // 对于执行工具，简化逻辑，移除后续提示
        if (tool.type === 'execution') {
            // 对于 search_docs，附加 link_prompt（保持向后兼容）
            if (['search_docs'].includes(name) && finalResult && !finalResult.startsWith("错误：")) {
                const linkPrompt = await _getLinkPrompt();
                if (linkPrompt) {
                    finalResult = `${finalResult}\n\n---\n\n${linkPrompt}`;
                }
            }
        }

        // 返回成功状态和结果
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
 * 从JSON字符串中解析 ask UI 指令（使用JsonParserService）
 */
function parseAskCall(jsonString: string): ParsedQuestion | null {
    if (typeof jsonString !== 'string') return null;

    // 直接使用 JsonParserService 解析
    const result = jsonParserService.parseLlmResponse(jsonString);
    const parsedResult = result ? result.toolCall : null;

    if (!parsedResult || parsedResult.tool !== 'ask_choice') {
        return null;
    }

    return {
        original: jsonString,
        question: parsedResult.question || '',
        suggestions: parsedResult.suggestions || []
    };
}

export function isToolRetryable(toolName: string): boolean {
    return ['search_docs', 'read_doc'].includes(toolName);
}

export { convertParams };

export default {
    parseToolCall,
    createStatusMessage,
    executeTool,
    parseAskCall,
    isToolRetryable,
};