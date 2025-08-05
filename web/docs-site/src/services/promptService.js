import yaml from 'js-yaml';
import logger from './loggerService.js';

const _agentNameCache = new Map();

/**
 * Resolves a relative path against a base path.
 * Handles '.' and '..' segments.
 * @param {string} basePath - The base path (should be a file path).
 * @param {string} relativePath - The relative path to resolve.
 * @returns {string} The resolved absolute path.
 */
function resolvePath(basePath, relativePath) {
    // If relativePath is absolute, return it directly
    if (relativePath.startsWith('/')) {
        return relativePath;
    }
    
    const baseParts = basePath.split('/').slice(0, -1); // remove filename
    const relativeParts = relativePath.split('/');
    
    for (const part of relativeParts) {
        if (part === '.') {
            continue;
        }
        if (part === '..') {
            if (baseParts.length > 0) {
                baseParts.pop();
            }
        } else {
            baseParts.push(part);
        }
    }
    return baseParts.join('/');
}

async function _fetchAgentName(domain, roleId) {
    const cacheKey = `${domain}-${roleId}`;
    if (_agentNameCache.has(cacheKey)) {
        return _agentNameCache.get(cacheKey);
    }

    try {
        const v = Date.now();
        const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;
        const roleConfigResponse = await fetch(`${roleConfigPath}?v=${v}`);
        if (!roleConfigResponse.ok) return '未知角色';

        const roleConfig = yaml.load(await roleConfigResponse.text());
        const personaPath = roleConfig?.customModes?.[0]?.persona;
        if (!personaPath) return '配置错误';

        const finalPersonaPath = resolvePath(roleConfigPath, personaPath);
        logger.log(`[PromptService] Fetching persona from: ${finalPersonaPath}`);
        const personaResponse = await fetch(`${finalPersonaPath}?v=${v}`);
        if (!personaResponse.ok) return '无名氏';

        const personaConfig = yaml.load(await personaResponse.text());
        const agentName = personaConfig?.name || 'AI';
        
        _agentNameCache.set(cacheKey, agentName);
        return agentName;
    } catch (error) {
        logger.error(`[PromptService] _fetchAgentName for '${roleId}' failed:`, error);
        return '加载失败';
    }
}

async function listAvailableAgents(domain) {
    try {
        const v = Date.now();
        const manifestPath = `/domains/${domain}/core/roles.json?v=${v}`;
        logger.log(`[PromptService] Listing available agents from: ${manifestPath}`);
        const response = await fetch(manifestPath);
        
        logger.log(`[PromptService] Manifest fetch response status: ${response.status}`);
        if (!response.ok) throw new Error(`无法加载 agent 清单: ${response.statusText}`);
        
        const roleInfos = await response.json();
        logger.log(`[PromptService] Loaded role infos:`, roleInfos);

        const agentsWithNames = await Promise.all(
            roleInfos.map(async (info) => {
                const name = await _fetchAgentName(domain, info.id);
                return { ...info, name };
            })
        );
        
        return agentsWithNames;
    } catch (error) {
        logger.error(`[PromptService] 获取可用 agent 列表失败 for domain ${domain}:`, error);
        return [];
    }
}

async function loadSystemPrompt(domain, roleId) {
    try {
        logger.log(`[PromptService] 开始为角色ID '${roleId}' 在域 '${domain}' 中加载模块化系统提示词...`);
        const v = Date.now();
        const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;

        const roleConfigResponse = await fetch(`${roleConfigPath}?v=${v}`);
        if (!roleConfigResponse.ok) {
            throw new Error(`无法加载角色配置文件: ${roleConfigResponse.statusText}`);
        }
        const roleConfigText = await roleConfigResponse.text();
        const roleConfig = yaml.load(roleConfigText);

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
        const globalToolsPath = `/prompts/tools_prompt.md`; // Global tools prompt path

        const [personaResponse, instructionsResponse, toolsResponse] = await Promise.all([
            fetch(`${finalPersonaPath}?v=${v}`),
            fetch(`${finalInstructionsPath}?v=${v}`),
            fetch(`${globalToolsPath}?v=${v}`) // Fetch from the global path
        ]);

        if (!personaResponse.ok) throw new Error(`无法加载 Persona 模块: ${personaResponse.statusText}`);
        if (!instructionsResponse.ok) throw new Error(`无法加载 Instructions 模块: ${instructionsResponse.statusText}`);
        if (!toolsResponse.ok) throw new Error(`无法加载全局 Tools 模块: ${toolsResponse.statusText}`);
        
        const personaText = await personaResponse.text();
        const instructionsPrompt = await instructionsResponse.text();
        const toolsPrompt = await toolsResponse.text();
        
        const personaConfig = yaml.load(personaText);
        const personaDefinition = personaConfig?.definition;
        const agentName = personaConfig?.name || 'AI';

        const finalSystemPrompt = `${personaDefinition}\n\n${instructionsPrompt}\n\n${toolsPrompt}`;
        logger.log("[PromptService] 模块化系统提示词加载并合并成功。");
        
        return {
            systemPrompt: finalSystemPrompt,
            agentName: agentName
        };
    } catch (error) {
        logger.error("[PromptService] 加载系统提示词失败:", error);
        return {
            systemPrompt: "你是一个AI助手。",
            agentName: "AI 助手"
        };
    }
}

export default {
    listAvailableAgents,
    loadSystemPrompt,
};