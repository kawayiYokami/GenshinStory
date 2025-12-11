import { FlatToolCall } from '@/features/agent/types';

// 定义工具调用接口，方便类型提示
interface ToolCallResult {
    toolCall: FlatToolCall;
    startIndex: number;
    endIndex: number;
}

/**
 * JSON 解析服务 - 增强版
 * 改进点：
 * 1. 使用堆栈平衡法提取 JSON，完美支持 JSON 后跟随文本的情况。
 * 2. 增加 JSON 容错修复（处理尾部逗号、非标准换行）。
 * 3. 简化归一化逻辑，减少误判。
 */
class JsonParserService {
    private readonly VALID_TOOLS = ['search_docs', 'read_doc', 'ask_choice'];

    /**
     * 主入口：解析 LLM 响应
     */
    public parseLlmResponse(text: string): ToolCallResult | null {
        if (!text || !text.trim()) return null;

        // 1. 预处理：移除 Markdown 代码块标记
        const cleanedText = this.stripCodeFences(text);

        // 2. 提取最外层的 JSON 字符串块（核心改进）
        const jsonBlock = this.extractFirstJsonBlock(cleanedText);

        if (!jsonBlock) {
            return null;
        }

        try {
            // 3. 尝试修复并解析
            const parsedObj = this.headerlessJsonParse(jsonBlock.jsonString);

            // 4. 结构归一化与工具识别
            const toolCall = this.normalizeToolCall(parsedObj);

            if (toolCall) {
                return {
                    toolCall,
                    startIndex: jsonBlock.startIndex, // 这里返回的是相对于 stripped text 的位置，实际应用可能需要映射回原文本
                    endIndex: jsonBlock.endIndex
                };
            }
        } catch (e) {
            console.warn('JSON parsing failed even after extraction:', e);
        }

        return null;
    }

    /**
     * 核心算法：基于括号计数的 JSON 提取器
     * 解决问题：JSON.parse 在末尾有杂乱文本时会失败，此方法能精准切分出 JSON 部分。
     */
    private extractFirstJsonBlock(text: string): { jsonString: string; startIndex: number; endIndex: number } | null {
        let firstOpen = text.indexOf('{');
        if (firstOpen === -1) return null;

        let depth = 0;
        let startIndex = -1;
        let inString = false;
        let escape = false;

        for (let i = firstOpen; i < text.length; i++) {
            const char = text[i];

            // 处理字符串内的字符，避免将字符串内的 } 误判为结束
            if (inString) {
                if (escape) {
                    escape = false;
                } else if (char === '\\') {
                    escape = true;
                } else if (char === '"') {
                    inString = false;
                }
                continue;
            }

            if (char === '"') {
                inString = true;
                continue;
            }

            if (char === '{') {
                if (depth === 0) startIndex = i;
                depth++;
            } else if (char === '}') {
                depth--;
                // 找到了最外层的闭合括号
                if (depth === 0 && startIndex !== -1) {
                    return {
                        jsonString: text.substring(startIndex, i + 1),
                        startIndex: startIndex,
                        endIndex: i + 1
                    };
                }
            }
        }

        return null;
    }

    /**
     * 容错解析：处理 LLM 常见的 JSON 语法错误
     */
    private headerlessJsonParse(jsonString: string): any {
        // 1. 基础尝试
        try {
            return JSON.parse(jsonString);
        } catch (e) {
            // 继续修复
        }

        // 2. 修复常见错误
        let repaired = jsonString
            // 移除尾部逗号 (Match: , })
            .replace(/,(\s*})/g, '$1')
            .replace(/,(\s*])/g, '$1')
            // 修复未转义的换行符 (将真实换行替换为 \n)
            .replace(/\n/g, '\\n')
            .replace(/\r/g, '')
            .replace(/\t/g, '\\t');

        try {
            return JSON.parse(repaired);
        } catch (e) {
            // 如果修复失败，抛出异常，外层会捕获
            throw e;
        }
    }

    /**
     * 将各种奇怪的结构（嵌套、feedback_data等）统一为扁平的工具调用对象
     */
    private normalizeToolCall(obj: any): FlatToolCall | null {
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return null;

        let target = obj;

        // 1. 处理 feedback_data (反转义逻辑)
        if (target.feedback_data) {
            try {
                const inner = typeof target.feedback_data === 'string'
                    ? JSON.parse(target.feedback_data)
                    : target.feedback_data;
                // 如果解析出来是对象，就用它替换当前层级
                if (typeof inner === 'object' && !Array.isArray(inner)) {
                    target = inner;
                }
            } catch (e) {
                // 解析失败则忽略，继续使用原对象
            }
        }

        // 2. 处理嵌套的 tool_call / function_call 包装
        if (target.tool_call || target.function_call || target.tool) {
            const wrapper = target.tool_call || target.function_call || target.tool;
            // 可能是 { tool_call: { name: "xx", arguments: {...} } }
            if (wrapper && typeof wrapper === 'object') {
                const name = wrapper.name || (typeof wrapper === 'string' ? wrapper : null);
                const args = wrapper.arguments || wrapper.args || wrapper.parameters || {};

                // 构造新对象
                target = { ...args };
                if (name) target.tool = name;
            }
        }

        // 3. 字段映射与工具推断
        const result: any = {};
        let detectedToolName: string | null = null;

        // 显式查找工具名字段
        if (target.tool && this.isValidToolName(target.tool)) detectedToolName = target.tool;
        else if (target.name && this.isValidToolName(target.name)) detectedToolName = target.name;
        // 兼容 key 为工具名的情况，例如 { "search_docs": "query..." }
        else {
            for (const key of Object.keys(target)) {
                if (this.isValidToolName(key)) {
                    detectedToolName = key;
                    // 特殊处理：如果是 ask_choice: { ... } 或 ask_choice: "..."
                    if (key === 'ask_choice') {
                        if (typeof target[key] === 'string') {
                            result.question = target[key];
                        } else if (typeof target[key] === 'object') {
                            Object.assign(result, target[key]);
                        }
                    } else if (typeof target[key] === 'string') {
                        // search_docs: "query" -> query: "query"
                        if (key === 'search_docs') result.query = target[key];
                        if (key === 'read_doc') result.path = target[key];
                    } else if (typeof target[key] === 'object' && target[key] !== null) {
                        // 处理完整参数对象格式，如 { "search_docs": { "query": "...", "maxResults": 10 } }
                        if (key === 'search_docs') {
                            Object.assign(result, target[key]);
                            result.tool = key;
                        }
                        if (key === 'read_doc') {
                            Object.assign(result, target[key]);
                            result.tool = key;
                        }
                    }
                    break;
                }
            }
        }

        if (!detectedToolName) return null;

        // 4. 组装最终结果，过滤无关字段
        result.tool = detectedToolName;

        // 复制其他有用字段
        for (const [key, value] of Object.entries(target)) {
            // 跳过已经是工具名的 key (除非它是结构体)
            if (key === detectedToolName && typeof value !== 'object') continue;
            if (key === 'tool' || key === 'name') continue;

            result[key] = value;
        }

        // 5. 针对 ask_choice 的 suggestions 特殊处理 (兼容数组形式)
        if (result.tool === 'ask_choice') {
            if (Array.isArray(target.suggestions)) {
                result.suggestions = target.suggestions;
            }
            // 兼容旧格式 { ask_choice: [suggestion1, suggestion2] }
            if (Array.isArray(target.ask_choice)) {
                result.suggestions = target.ask_choice;
            }
        }

        return result as FlatToolCall;
    }

    private stripCodeFences(text: string): string {
        return text.replace(/```json/gi, '').replace(/```/g, '').trim();
    }

    private isValidToolName(name: string): boolean {
        return this.VALID_TOOLS.includes(name);
    }
}

export default new JsonParserService();