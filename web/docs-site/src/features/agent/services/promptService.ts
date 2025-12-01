import yaml from 'js-yaml';
import logger from '../../app/services/loggerService';
import { toolPromptService } from './toolPromptService';

// --- 类型定义 ---
interface RoleInfo {
    id: string;
    description: string;
    [key: string]: any;
}

interface AgentInfo extends RoleInfo {
    name: string;
    isCustom?: boolean;
}

interface SystemPromptResult {
    systemPrompt: string;
    agentName: string;
}

interface RoleConfig {
    customModes?: Array<{
        persona?: string;
        // instructions?: string; // Removed
    }>;
}

interface PersonaConfig {
    name?: string;
    definition?: string;
}

export interface InstructionInfo {
    id: string;
    name: string;
    path: string;
    content?: string; // For custom instructions
    isCustom?: boolean; // To differentiate custom instructions
}

export interface CustomPersona {
    id: string;
    name: string;
    description: string;
    content: string; // The persona definition prompt
    isCustom: boolean;
}

const _agentNameCache = new Map<string, string | Promise<string>>();
const _systemPromptCache = new Map<string, { result: SystemPromptResult; timestamp: number } | Promise<SystemPromptResult>>();
const _instructionsCache = new Map<string, InstructionInfo[] | Promise<InstructionInfo[]>>();

const CACHE_TTL = 60 * 60 * 1000; // 1小时缓存过期时间（毫秒）

/**
 * 根据基本路径解析相对路径。
 * @param basePath 基本路径（应为文件路径）
 * @param relativePath 要解析的相对路径
 * @returns 解析后的绝对路径
 */
function resolvePath(basePath: string, relativePath: string): string {
    if (relativePath.startsWith('/')) {
        return relativePath;
    }

    const baseParts = basePath.split('/').slice(0, -1);
    const relativeParts = relativePath.split('/');

    for (const part of relativeParts) {
        if (part === '.') continue;
        if (part === '..') {
            if (baseParts.length > 0) baseParts.pop();
        } else {
            baseParts.push(part);
        }
    }
    return baseParts.join('/');
}

// --- Custom Instructions Management ---

const CUSTOM_INSTRUCTIONS_KEY = 'customInstructions';
const CUSTOM_PERSONAS_KEY = 'customPersonas';

function getCustomInstructions(): InstructionInfo[] {
    try {
        const stored = localStorage.getItem(CUSTOM_INSTRUCTIONS_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (error) {
        logger.error('[PromptService] 从 LocalStorage 加载自定义指令失败:', error);
        return [];
    }
}

function saveCustomInstructions(customInstructions: InstructionInfo[]): void {
    try {
        localStorage.setItem(CUSTOM_INSTRUCTIONS_KEY, JSON.stringify(customInstructions));
    } catch (error) {
        logger.error('[PromptService] 保存自定义指令到 LocalStorage 失败:', error);
    }
}

export function addCustomInstruction(name: string, content: string): InstructionInfo {
    const newInstruction: InstructionInfo = {
        id: `custom_${Date.now()}`,
        name,
        path: '', // Not used for custom instructions
        content,
        isCustom: true,
    };

    const customInstructions = getCustomInstructions();
    customInstructions.push(newInstruction);
    saveCustomInstructions(customInstructions);

    // Clear the instructions cache to force a refresh
    _instructionsCache.delete('instructions');

    logger.log(`[PromptService] 已添加自定义指令: "${name}"`);
    return newInstruction;
}

export function removeCustomInstruction(id: string): boolean {
    const customInstructions = getCustomInstructions();
    const index = customInstructions.findIndex(item => item.id === id);

    if (index === -1) {
        logger.warn(`[PromptService] 未找到要删除的自定义指令: "${id}"`);
        return false;
    }

    const removedInstruction = customInstructions.splice(index, 1)[0];
    saveCustomInstructions(customInstructions);

    // Clear the instructions cache to force a refresh
    _instructionsCache.delete('instructions');

    logger.log(`[PromptService] 已删除自定义指令: "${removedInstruction.name}"`);
    return true;
}

// --- Custom Personas Management ---

function getCustomPersonas(): CustomPersona[] {
    try {
        const stored = localStorage.getItem(CUSTOM_PERSONAS_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (error) {
        logger.error('[PromptService] 从 LocalStorage 加载自定义角色失败:', error);
        return [];
    }
}

function saveCustomPersonas(customPersonas: CustomPersona[]): void {
    try {
        localStorage.setItem(CUSTOM_PERSONAS_KEY, JSON.stringify(customPersonas));
    } catch (error) {
        logger.error('[PromptService] 保存自定义角色到 LocalStorage 失败:', error);
    }
}

export function addCustomPersona(name: string, content: string): CustomPersona {
    const newPersona: CustomPersona = {
        id: `custom_persona_${Date.now()}`,
        name,
        description: '自定义角色',
        content,
        isCustom: true,
    };

    const customPersonas = getCustomPersonas();
    customPersonas.push(newPersona);
    saveCustomPersonas(customPersonas);

    // Clear caches
    _agentNameCache.clear();

    logger.log(`[PromptService] 已添加自定义角色: "${name}"`);
    return newPersona;
}

export function removeCustomPersona(id: string): boolean {
    const customPersonas = getCustomPersonas();
    const index = customPersonas.findIndex(item => item.id === id);

    if (index === -1) {
        logger.warn(`[PromptService] 未找到要删除的自定义角色: "${id}"`);
        return false;
    }

    const removedPersona = customPersonas.splice(index, 1)[0];
    saveCustomPersonas(customPersonas);

    // Clear caches
    _agentNameCache.clear();

    logger.log(`[PromptService] 已删除自定义角色: "${removedPersona.name}"`);
    return true;
}

async function listAvailableInstructions(): Promise<InstructionInfo[]> {
    const cacheKey = 'instructions';
    const cached = _instructionsCache.get(cacheKey);

    if (cached && !(cached instanceof Promise)) return cached;
    if (cached instanceof Promise) return cached;

    const loadPromise = (async () => {
        try {
            // Fetch static instructions
            const v = Date.now();
            const response = await fetch(`/prompts/agent/instructions.json?v=${v}`);
            if (!response.ok) throw new Error('无法加载指令列表');
            const staticInstructions = await response.json() as InstructionInfo[];

            // Get custom instructions
            const customInstructions = getCustomInstructions();

            // Combine and cache
            const allInstructions = [...customInstructions, ...staticInstructions];
            _instructionsCache.set(cacheKey, allInstructions);
            return allInstructions;
        } catch (error) {
            logger.error('[PromptService] 加载指令列表失败:', error);
            _instructionsCache.delete(cacheKey);
            // Fallback to custom instructions only
            return getCustomInstructions();
        }
    })();

    _instructionsCache.set(cacheKey, loadPromise);
    return loadPromise;
}

async function _fetchAgentName(domain: string, roleId: string): Promise<string> {
    // 验证输入参数，防止缓存键冲突
    if (!domain || !roleId) {
        logger.error("[PromptService] _fetchAgentName: 缺少必要参数", { domain, roleId });
        return '参数错误';
    }

    const cacheKey = `${domain}|${roleId}`; // 使用更安全的分隔符
    const cached = _agentNameCache.get(cacheKey);

    // 如果缓存中已有结果，直接返回
    if (cached && !(cached instanceof Promise)) {
        return cached;
    }

    // 如果缓存中已有正在进行的 Promise，直接返回该 Promise
    if (cached instanceof Promise) {
        try {
            return await cached;
        } catch (error) {
            // Promise 已经失败，从缓存中移除并继续重新加载
            _agentNameCache.delete(cacheKey);
            logger.error("[PromptService] 缓存的 _fetchAgentName Promise 失败:", error);
        }
    }

    // 创建新的 Promise 并立即存入缓存
    const loadPromise = (async () => {
        try {
            const v = Date.now();
            const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;
            const roleConfigResponse = await fetch(`${roleConfigPath}?v=${v}`);
            if (!roleConfigResponse.ok) return '未知角色';

            const roleConfig = yaml.load(await roleConfigResponse.text()) as RoleConfig;
            const personaPath = roleConfig?.customModes?.[0]?.persona;
            if (!personaPath) return '配置错误';

            const finalPersonaPath = resolvePath(roleConfigPath, personaPath);
            const personaResponse = await fetch(`${finalPersonaPath}?v=${v}`);
            if (!personaResponse.ok) return '无名氏';

            const personaConfig = yaml.load(await personaResponse.text()) as PersonaConfig;
            const agentName = personaConfig?.name || 'AI';

            // 将结果存入缓存，替换 Promise
            _agentNameCache.set(cacheKey, agentName);
            return agentName;
        } catch (error) {
            // 发生错误时，从缓存中移除该 Promise
            _agentNameCache.delete(cacheKey);
            logger.error(`[PromptService] _fetchAgentName for '${roleId}' 失败:`, error);
            return '加载失败';
        }
    })();

    // 将 Promise 存入缓存
    _agentNameCache.set(cacheKey, loadPromise);

    return loadPromise;
}

async function listAvailableAgents(domain: string): Promise<AgentInfo[]> {
    try {
        const v = Date.now();
        const manifestPath = `/domains/${domain}/core/roles.json?v=${v}`;
        const response = await fetch(manifestPath);

        if (!response.ok) throw new Error(`无法加载 agent 清单: ${response.statusText}`);

        const roleInfos: RoleInfo[] = await response.json();

        const agentsWithNames = await Promise.all(
            roleInfos.map(async (info) => {
                const name = await _fetchAgentName(domain, info.id);
                return { ...info, name };
            })
        );

        // Get custom personas and format them as agents
        const customPersonas = getCustomPersonas();
        const customAgents: AgentInfo[] = customPersonas.map(p => ({
            id: p.id,
            name: p.name,
            description: p.description,
            isCustom: true
        }));

        return [...agentsWithNames, ...customAgents];
    } catch (error) {
        logger.error(`[PromptService] 获取域 ${domain} 的可用 agent 列表失败:`, error);
        // Even if fetching remote agents fails, return custom ones
        const customPersonas = getCustomPersonas();
        return customPersonas.map(p => ({
            id: p.id,
            name: p.name,
            description: p.description,
            isCustom: true
        }));
    }
}

async function loadSystemPrompt(domain: string, roleId: string, instructionId: string = 'chat'): Promise<SystemPromptResult> {
    // 验证输入参数，防止缓存键冲突
    if (!domain || !roleId) {
        logger.error("[PromptService] loadSystemPrompt: 缺少必要参数", { domain, roleId });
        return {
            systemPrompt: "参数错误，请提供有效的域和角色ID。",
            agentName: "参数错误"
        };
    }

    const cacheKey = `${domain}|${roleId}|${instructionId}`; // 增加指令ID到缓存键
    const cached = _systemPromptCache.get(cacheKey);

    // 检查缓存是否过期
    let isExpired = false;
    if (cached && !(cached instanceof Promise)) {
        isExpired = Date.now() - cached.timestamp > CACHE_TTL;
    }

    // 如果缓存中已有未过期的结果，直接返回
    if (cached && !(cached instanceof Promise) && !isExpired) {
        return cached.result;
    }

    // 如果缓存中已有正在进行的 Promise，直接返回该 Promise
    if (cached instanceof Promise) {
        try {
            return await cached;
        } catch (error) {
            // Promise 已经失败，从缓存中移除并继续重新加载
            _systemPromptCache.delete(cacheKey);
            logger.error("[PromptService] 缓存的 Promise 失败:", error);
        }
    }

    // 创建新的 Promise 并立即存入缓存
    const loadPromise = (async () => {
        try {
            const v = Date.now();

            // Check if it's a custom persona
            const customPersonas = getCustomPersonas();
            const customPersona = customPersonas.find(p => p.id === roleId);

            let personaDefinition = '';
            let agentName = '';

            if (customPersona) {
                personaDefinition = customPersona.content;
                agentName = customPersona.name;
            } else {
                // Load from file for standard roles
                const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;

                const roleConfigResponse = await fetch(`${roleConfigPath}?v=${v}`);
                if (!roleConfigResponse.ok) {
                    throw new Error(`无法加载角色配置文件: ${roleConfigResponse.statusText}`);
                }
                const roleConfigText = await roleConfigResponse.text();
                const roleConfig = yaml.load(roleConfigText) as RoleConfig;

                const activeMode = roleConfig?.customModes?.[0];
                if (!activeMode) {
                    throw new Error("在角色配置中找不到有效的 'customModes'。");
                }

                const { persona: personaPath } = activeMode;
                if (!personaPath) {
                    throw new Error("角色配置中缺少 'persona' 的路径。");
                }

                const finalPersonaPath = resolvePath(roleConfigPath, personaPath);

                const personaResponse = await fetch(`${finalPersonaPath}?v=${v}`);
                if (!personaResponse.ok) throw new Error(`无法加载 Persona 模块: ${personaResponse.statusText}`);

                const personaText = await personaResponse.text();
                const personaConfig = yaml.load(personaText) as PersonaConfig;
                personaDefinition = personaConfig?.definition || '';
                agentName = personaConfig?.name || 'AI';
            }

            // 获取指令
            const instructionsList = await listAvailableInstructions();
            const instruction = instructionsList.find(i => i.id === instructionId) || instructionsList.find(i => i.id === 'chat');

            let instructionsPrompt = '';
            if (instruction) {
                if (instruction.isCustom && instruction.content) {
                    // It's a custom instruction, use its content directly
                    instructionsPrompt = instruction.content;
                } else if (instruction.path) {
                    // It's a static instruction, fetch from file
                    const instructionPath = `/prompts/agent/${instruction.path}`;
                    const instructionsResponse = await fetch(`${instructionPath}?v=${v}`);
                    if (!instructionsResponse.ok) throw new Error(`无法加载 Instructions 模块: ${instructionsResponse.statusText}`);
                    instructionsPrompt = await instructionsResponse.text();
                }
            }

            if (!instructionsPrompt) {
                // Fallback to default chat.md if instruction was not found or failed to load
                const fallbackInstructionPath = `/prompts/agent/chat.md`;
                const fallbackResponse = await fetch(`${fallbackInstructionPath}?v=${v}`);
                if (!fallbackResponse.ok) throw new Error(`无法加载默认指令模块: ${fallbackResponse.statusText}`);
                instructionsPrompt = await fallbackResponse.text();
            }

            // 加载原子化工具提示词
            await toolPromptService.loadToolPrompts();
            const toolsPrompt = toolPromptService.getSystemPrompt();

            const finalSystemPrompt = `${personaDefinition}\n\n${instructionsPrompt}\n\n${toolsPrompt}`;

            const result = {
                systemPrompt: finalSystemPrompt,
                agentName: agentName
            };

            // 将结果和时间戳存入缓存，替换 Promise
            _systemPromptCache.set(cacheKey, { result, timestamp: Date.now() });
            return result;
        } catch (error) {
            // 发生错误时，从缓存中移除该 Promise
            _systemPromptCache.delete(cacheKey);
            logger.error("[PromptService] 加载系统提示词失败:", error);

            // 返回默认结果而不是抛出错误，确保应用继续运行
            const fallbackResult = {
                systemPrompt: "你是一个AI助手。",
                agentName: "AI 助手"
            };

            return fallbackResult;
        }
    })();

    // 将 Promise 存入缓存
    _systemPromptCache.set(cacheKey, loadPromise);

    return loadPromise;
}

export default {
    listAvailableAgents,
    loadSystemPrompt,
    listAvailableInstructions,
    addCustomInstruction,
    removeCustomInstruction,
    addCustomPersona,
    removeCustomPersona,
};