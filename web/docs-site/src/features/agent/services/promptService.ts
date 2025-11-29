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
}

interface SystemPromptResult {
    systemPrompt: string;
    agentName: string;
}

interface RoleConfig {
    customModes?: Array<{
        persona?: string;
        instructions?: string;
    }>;
}

interface PersonaConfig {
    name?: string;
    definition?: string;
}

const _agentNameCache = new Map<string, string | Promise<string>>();
const _systemPromptCache = new Map<string, { result: SystemPromptResult; timestamp: number } | Promise<SystemPromptResult>>();

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

        return agentsWithNames;
    } catch (error) {
        logger.error(`[PromptService] 获取域 ${domain} 的可用 agent 列表失败:`, error);
        return [];
    }
}

async function loadSystemPrompt(domain: string, roleId: string): Promise<SystemPromptResult> {
    // 验证输入参数，防止缓存键冲突
    if (!domain || !roleId) {
        logger.error("[PromptService] loadSystemPrompt: 缺少必要参数", { domain, roleId });
        return {
            systemPrompt: "参数错误，请提供有效的域和角色ID。",
            agentName: "参数错误"
        };
    }

    const cacheKey = `${domain}|${roleId}`; // 使用更安全的分隔符
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

            const { persona: personaPath, instructions: instructionsPath } = activeMode;
            if (!personaPath || !instructionsPath) {
                throw new Error("角色配置中缺少 'persona' 或 'instructions' 的路径。");
            }

            const finalPersonaPath = resolvePath(roleConfigPath, personaPath);
            const finalInstructionsPath = resolvePath(roleConfigPath, instructionsPath);

            const [personaResponse, instructionsResponse] = await Promise.all([
                fetch(`${finalPersonaPath}?v=${v}`),
                fetch(`${finalInstructionsPath}?v=${v}`)
            ]);

            if (!personaResponse.ok) throw new Error(`无法加载 Persona 模块: ${personaResponse.statusText}`);
            if (!instructionsResponse.ok) throw new Error(`无法加载 Instructions 模块: ${instructionsResponse.statusText}`);

            const personaText = await personaResponse.text();
            const instructionsPrompt = await instructionsResponse.text();

            const personaConfig = yaml.load(personaText) as PersonaConfig;
            const personaDefinition = personaConfig?.definition;
            const agentName = personaConfig?.name || 'AI';

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
};