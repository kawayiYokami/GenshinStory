import yaml from 'js-yaml';
import logger from './loggerService.js';

const _agentNameCache = new Map();

async function _fetchAgentName(roleId) {
    if (_agentNameCache.has(roleId)) {
        return _agentNameCache.get(roleId);
    }

    try {
        const v = Date.now();
        const roleConfigPath = `/prompts/roles/${roleId}.yaml?v=${v}`;
        const roleConfigResponse = await fetch(roleConfigPath);
        if (!roleConfigResponse.ok) return '未知角色';

        const roleConfig = yaml.load(await roleConfigResponse.text());
        const personaPath = roleConfig?.customModes?.[0]?.persona;
        if (!personaPath) return '配置错误';

        const personaResponse = await fetch(`${personaPath}?v=${v}`);
        if (!personaResponse.ok) return '无名氏';

        const personaConfig = yaml.load(await personaResponse.text());
        const agentName = personaConfig?.name || 'AI';
        
        _agentNameCache.set(roleId, agentName);
        return agentName;
    } catch (error) {
        logger.error(`[PromptService] 获取 '${roleId}' 名称失败:`, error);
        return '加载失败';
    }
}

async function listAvailableAgents(game) {
    try {
        const v = Date.now();
        const manifestPath = `/prompts/roles/manifest.json?v=${v}`;
        const response = await fetch(manifestPath);
        if (!response.ok) throw new Error(`无法加载 agent 清单: ${response.statusText}`);
        
        const manifest = await response.json();
        const roleInfos = manifest[game] || [];

        const agentsWithNames = await Promise.all(
            roleInfos.map(async (info) => {
                const name = await _fetchAgentName(info.id);
                return { ...info, name };
            })
        );
        
        return agentsWithNames;
    } catch (error) {
        logger.error("[PromptService] 获取可用 agent 列表失败:", error);
        return [];
    }
}

async function loadSystemPrompt(roleId) {
    try {
        logger.log(`[PromptService] 开始为角色ID '${roleId}' 加载模块化系统提示词...`);
        const v = Date.now();
        const roleConfigPath = `/prompts/roles/${roleId}.yaml?v=${v}`;

        const roleConfigResponse = await fetch(roleConfigPath);
        if (!roleConfigResponse.ok) {
            throw new Error(`无法加载角色配置文件: ${roleConfigResponse.statusText}`);
        }
        const roleConfigText = await roleConfigResponse.text();
        const roleConfig = yaml.load(roleConfigText);

        const activeMode = roleConfig?.customModes?.[0];
        if (!activeMode) {
            throw new Error("在角色配置中找不到有效的 'customModes'。");
        }

        const { persona: personaPath, instructions: instructionsPath, tools: toolsPath } = activeMode;
        if (!personaPath || !instructionsPath || !toolsPath) {
            throw new Error("角色配置中缺少 'persona', 'instructions', 或 'tools' 的路径。");
        }

        const [personaResponse, instructionsResponse, toolsResponse] = await Promise.all([
            fetch(`${personaPath}?v=${v}`),
            fetch(`${instructionsPath}?v=${v}`),
            fetch(`${toolsPath}?v=${v}`)
        ]);

        if (!personaResponse.ok) throw new Error(`无法加载 Persona 模块: ${personaResponse.statusText}`);
        if (!instructionsResponse.ok) throw new Error(`无法加载 Instructions 模块: ${instructionsResponse.statusText}`);
        if (!toolsResponse.ok) throw new Error(`无法加载 Tools 模块: ${toolsResponse.statusText}`);
        
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