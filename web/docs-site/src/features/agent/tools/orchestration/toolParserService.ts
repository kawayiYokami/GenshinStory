/**
 * @fileoverview 工具解析服务
 * @description 提供工具调用相关的辅助函数
 *
 * 注意：工具执行已迁移到 SDK 自动管理（通过 toolRegistryService 中的 execute 函数）
 * 此文件保留用于工具状态消息和错误处理
 */

import logger from '../../../app/services/loggerService';
import { toolPromptService } from '../implementations/toolPromptService';
import { toolRegistryService } from '../registry/toolRegistryService';

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

let linkPromptContent: string | null = null;

/**
 * 智能转换工具参数（支持平铺和嵌套格式）
 */
function convertParams(toolName: string, params: Record<string, any>): ToolCallParams {
    const converted: ToolCallParams = {};

    for (const [key, value] of Object.entries(params)) {
        if (typeof value === 'string' || typeof value === 'number') {
            converted[key] = value;
        } else if (Array.isArray(value)) {
            converted[key] = value;
        } else if (typeof value === 'object' && value !== null) {
            converted[key] = JSON.stringify(value);
        } else {
            converted[key] = String(value);
        }
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
 * 为工具调用创建面向用户的状态消息
 */
function createStatusMessage(parsedTool: ParsedToolCall): string {
    const { name, params } = parsedTool;
    switch (name) {
        case 'search_docs':
            return `正在搜索 "${params.query || params.regex || ''}" 的相关文档...`;
        case 'read_doc':
            return `正在读取文档...`;
        default:
            return `正在执行工具: ${name}...`;
    }
}

/**
 * 执行工具（供 SDK 自动调用使用）
 * @deprecated 工具执行已迁移到 toolRegistryService.toSdkToolDefinitions 中的 execute 函数
 */
async function executeTool(parsedTool: ParsedToolCall): Promise<{ status: 'success' | 'error'; result: string; followUpPrompt?: string }> {
    const { name, params } = parsedTool;
    logger.log(`[ToolParserService] 准备执行工具: ${name}`, params);

    try {
        // 从工具注册表获取工具实例
        const tool = toolRegistryService.getTool(name);
        if (!tool) {
            const errorMessage = `错误：未知的工具 '${name}'`;
            logger.error(`[ToolParserService] 尝试调用一个未知的工具: ${name}`);
            return { status: 'error', result: errorMessage };
        }

        // UI工具不执行后端逻辑
        if (tool.type === 'ui') {
            return { status: 'success', result: '' };
        }

        // 执行工具
        const executionResult = await tool.execute(params);
        let finalResult = executionResult.result;

        // 对于 search_docs，附加 link_prompt
        if (name === 'search_docs' && finalResult && !finalResult.startsWith("错误：")) {
            const linkPrompt = await _getLinkPrompt();
            if (linkPrompt) {
                finalResult = `${finalResult}\n\n---\n\n${linkPrompt}`;
            }
        }

        return {
            status: 'success',
            result: finalResult,
            followUpPrompt: executionResult.followUpPrompt
        };
    } catch (e: any) {
        const errorMessage = `错误：执行工具 '${name}' 时发生异常: ${e.message}`;
        logger.error(`[ToolParserService] 执行工具 '${name}' 异常:`, e);
        return { status: 'error', result: errorMessage };
    }
}

export function isToolRetryable(toolName: string): boolean {
    return ['search_docs', 'read_doc'].includes(toolName);
}

export { convertParams };

export default {
    createStatusMessage,
    executeTool,
    isToolRetryable,
};
