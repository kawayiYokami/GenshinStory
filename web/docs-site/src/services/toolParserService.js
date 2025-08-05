import logger from './loggerService.js';
import localTools from './localToolsService.js';
import tokenizer from './tokenizerService.js';

const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs'];
let linkPromptContent = null;

async function _getLinkPrompt() {
    if (linkPromptContent) {
        return linkPromptContent;
    }
    try {
        const v = Date.now();
        const response = await fetch(`/prompts/link_prompt.md?v=${v}`);
        if (!response.ok) {
            logger.error("无法加载 link_prompt.md");
            return ""; // 失败时返回空字符串
        }
        linkPromptContent = await response.text();
        return linkPromptContent;
    } catch (error) {
        logger.error("加载 link_prompt.md 时出错:", error);
        return "";
    }
}

/**
 * Parses a tool call from the API's structured JSON format.
 * @param {object} toolCall - The tool_call object from the API response.
 * @returns {{name: string, params: object, xml: string}|null} The parsed tool call or null.
 */
function parseJsonToolCall(toolCall) {
    if (!toolCall || !toolCall.function) return null;
    
    const { name, arguments: args } = toolCall.function;

    if (!VALID_TOOLS.includes(name)) {
        logger.log(`[ToolParser] Parsed a JSON tool call for "<${name}>", but it's not in the VALID_TOOLS whitelist. Ignoring.`);
        return null;
    }

    try {
        const params = JSON.parse(args);
        return {
            name,
            params,
            // We don't have a raw XML string here, but we can create a representative one for logging/consistency.
            xml: `<${name}>${JSON.stringify(params)}</${name}>`
        };
    } catch (error) {
        logger.error(`[ToolParser] Error parsing JSON arguments for tool '${name}':`, error);
        return null;
    }
}


/**
 * Parses an XML-like string to find a tool call.
 * @param {string} xmlString The string to parse.
 * @returns {{name: string, params: object, xml: string}|null} The parsed tool call or null.
 */
function parseXmlToolCall(xmlString) {
    if (typeof xmlString !== 'string') return null;

    const toolCallRegex = /<([a-zA-Z0-9_]+)>([\s\S]*?)<\/\1>/;
    const match = xmlString.match(toolCallRegex);

    if (!match) return null;

    const toolName = match[1];

    if (!VALID_TOOLS.includes(toolName)) {
        logger.log(`[ToolParser] Parsed an XML tag "<${toolName}>", but it's not in the VALID_TOOLS whitelist. Ignoring.`);
        return null;
    }

    const fullXml = match[0];
    const innerContent = match[2].trim();
    
    const params = {};
    const paramRegex = /<([a-zA-Z0-9_]+)>([\s\S]*?)<\/(\1)>/g;
    let paramMatch;
    
    while ((paramMatch = paramRegex.exec(innerContent)) !== null) {
        params[paramMatch[1]] = paramMatch[2].trim();
    }

    // If no <param> tags found, assume the whole inner content is the 'args'
    if (Object.keys(params).length === 0 && innerContent) {
        params.args = innerContent;
    }

    return { name: toolName, params, xml: fullXml };
}

/**
 * Parses the arguments for a read_doc tool call.
 * @param {string} argsContent The content of the <args> tag.
 * @returns {Array<{path: string, lineRanges: Array<string>}>} An array of document requests.
 */
function parseReadDocRequests(argsContent) {
    const docRequests = [];
    if (argsContent && typeof argsContent === 'string') {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(`<root>${argsContent}</root>`, "text/xml");
        const docNodes = xmlDoc.querySelectorAll("doc");

        if (docNodes.length > 0) {
            docNodes.forEach(docNode => {
                const pathNode = docNode.querySelector("path");
                if (pathNode && pathNode.textContent) {
                    const request = { path: pathNode.textContent.trim(), lineRanges: [] };
                    const rangeNodes = docNode.querySelectorAll("line_range");
                    rangeNodes.forEach(rangeNode => {
                        if (rangeNode.textContent) {
                            request.lineRanges.push(rangeNode.textContent.trim());
                        }
                    });
                    docRequests.push(request);
                }
            });
        } else {
            // Fallback for simple <path> without <doc> wrapper
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
 * Creates a user-facing status message for a tool call.
 * @param {object} parsedTool - The parsed tool object.
 * @returns {string} The status message.
 */
function createStatusMessage(parsedTool) {
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
 * Executes a tool and handles all related logic like result processing and error handling.
 * @param {object} parsedTool - The parsed tool object.
 * @returns {string} The final, processed tool result string.
 */
async function executeTool(parsedTool) {
    const { name, params } = parsedTool;
    logger.log(`[ToolCoordinator] 准备执行工具: ${name}`, params);
    
    let toolResult;
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
    } catch (e) {
        toolResult = `错误：执行工具 '${name}' 时发生异常: ${e.message}`;
        logger.error(`[ToolCoordinator] 执行工具 '${name}' 异常:`, e);
    }

    // --- Result Post-processing ---

    // Add reference prompt for specific tools
    if (['search_docs', 'list_docs'].includes(name) && toolResult && !toolResult.startsWith("错误：")) {
        const linkPrompt = await _getLinkPrompt();
        if (linkPrompt) {
            toolResult = `${linkPrompt}\n\n---\n\n${toolResult}`;
        }
    }

    return toolResult;
}

/**
 * Parses an <ask_question> UI instruction from a string.
 * @param {string} xmlString The string to parse.
 * @returns {{xml: string, question: string, suggestions: Array<string>}|null}
 */
function parseAskQuestionCall(xmlString) {
    if (typeof xmlString !== 'string') return null;

    // 更新正则表达式以匹配 <ask_question>
    const askQuestionRegex = /<ask_question>([\s\S]*?)<\/ask_question>/;
    const match = xmlString.match(askQuestionRegex);

    if (!match) return null;

    const fullXml = match[0];
    const innerContent = match[1].trim();
    
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(`<root>${innerContent}</root>`, "text/xml");

    const questionNode = xmlDoc.querySelector("question");
    const suggestNodes = xmlDoc.querySelectorAll("suggest");

    // 严格校验：必须有 question 标签且内容不为空
    if (!questionNode || !questionNode.textContent) {
        logger.warn('[ToolParser] Parsed <ask_question> but found no valid <question> tag inside. Ignoring.');
        return null;
    }

    const suggestions = Array.from(suggestNodes).map(node => node.textContent.trim());

    // 严格校验：建议数量必须在 2 到 4 个之间，否则忽略
    if (suggestions.length < 2 || suggestions.length > 4) {
        logger.warn(`[ToolParser] Parsed <ask_question> but found ${suggestions.length} suggestions (expected 2-4). Ignoring.`);
        return null;
    }

    return {
        xml: fullXml,
        question: questionNode.textContent.trim(),
        suggestions: suggestions
    };
}

export default {
    parseXmlToolCall,
    parseJsonToolCall,
    parseReadDocRequests,
    createStatusMessage,
    executeTool,
    parseAskQuestionCall,
};