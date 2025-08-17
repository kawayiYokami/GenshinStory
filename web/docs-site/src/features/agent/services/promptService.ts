import yaml from 'js-yaml';
import logger from '../../app/services/loggerService';

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

const _agentNameCache = new Map<string, string>();

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
    const cacheKey = `${domain}-${roleId}`;
    if (_agentNameCache.has(cacheKey)) {
        return _agentNameCache.get(cacheKey) as string;
    }

    try {
        const v = Date.now();
        const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;
        const roleConfigResponse = await fetch(`${roleConfigPath}?v=${v}`);
        if (!roleConfigResponse.ok) return '未知角色';

        const roleConfig = yaml.load(await roleConfigResponse.text()) as any;
        const personaPath = roleConfig?.customModes?.[0]?.persona;
        if (!personaPath) return '配置错误';

        const finalPersonaPath = resolvePath(roleConfigPath, personaPath);
        logger.log(`[PromptService] 正在从以下位置获取角色信息: ${finalPersonaPath}`);
        const personaResponse = await fetch(`${finalPersonaPath}?v=${v}`);
        if (!personaResponse.ok) return '无名氏';

        const personaConfig = yaml.load(await personaResponse.text()) as any;
        const agentName = personaConfig?.name || 'AI';
        
        _agentNameCache.set(cacheKey, agentName);
        return agentName;
    } catch (error) {
        logger.error(`[PromptService] _fetchAgentName for '${roleId}' 失败:`, error);
        return '加载失败';
    }
}

async function listAvailableAgents(domain: string): Promise<AgentInfo[]> {
    try {
        const v = Date.now();
        const manifestPath = `/domains/${domain}/core/roles.json?v=${v}`;
        logger.log(`[PromptService] 正在从以下位置列出可用 agent: ${manifestPath}`);
        const response = await fetch(manifestPath);
        
        logger.log(`[PromptService] 清单获取响应状态: ${response.status}`);
        if (!response.ok) throw new Error(`无法加载 agent 清单: ${response.statusText}`);
        
        const roleInfos: RoleInfo[] = await response.json();
        logger.log(`[PromptService] 已加载的角色信息:`, roleInfos);

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
    try {
        logger.log(`[PromptService] 开始为域 '${domain}' 中的角色ID '${roleId}' 加载模块化系统提示词...`);
        const v = Date.now();
        const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;

        const roleConfigResponse = await fetch(`${roleConfigPath}?v=${v}`);
        if (!roleConfigResponse.ok) {
            throw new Error(`无法加载角色配置文件: ${roleConfigResponse.statusText}`);
        }
        const roleConfigText = await roleConfigResponse.text();
        const roleConfig = yaml.load(roleConfigText) as any;

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
        const globalToolsPath = `/prompts/tools_prompt.md`;

        const [personaResponse, instructionsResponse, toolsResponse] = await Promise.all([
            fetch(`${finalPersonaPath}?v=${v}`),
            fetch(`${finalInstructionsPath}?v=${v}`),
            fetch(`${globalToolsPath}?v=${v}`)
        ]);

        if (!personaResponse.ok) throw new Error(`无法加载 Persona 模块: ${personaResponse.statusText}`);
        if (!instructionsResponse.ok) throw new Error(`无法加载 Instructions 模块: ${instructionsResponse.statusText}`);
        if (!toolsResponse.ok) throw new Error(`无法加载全局 Tools 模块: ${toolsResponse.statusText}`);
        
        const personaText = await personaResponse.text();
        const instructionsPrompt = await instructionsResponse.text();
        const toolsPrompt = await toolsResponse.text();
        
        const personaConfig = yaml.load(personaText) as any;
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