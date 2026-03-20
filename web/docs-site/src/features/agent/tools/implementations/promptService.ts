import yaml from 'js-yaml';
import logger from '../../../app/services/loggerService';
import { toolPromptService } from './toolPromptService';
import { useDataStore } from '@/features/app/stores/data';
import filePathService from '@/features/app/services/filePathService';
import storageFacade from '@/features/app/services/storageFacade';

// --- 类型定义 ---
interface DirectoryNode {
    name: string;
    isDirectory: boolean;
    children?: DirectoryNode[];
}

interface RoleInfo {
    id: string;
    description: string;
    [key: string]: any;
}

interface RoleUiConfig {
    icon?: string;
    memePack?: string;
}

interface AgentInfo extends RoleInfo {
    name: string;
    isCustom?: boolean;
    icon?: string;
    memePack?: string;
}

interface SystemPromptResult {
    systemPrompt: string;
    agentName: string;
}

interface RoleConfig {
    ui?: RoleUiConfig;
    customModes?: Array<{
        persona?: string;
        // instructions?: string; // Removed
    }>;
}

interface PersonaConfig {
    name?: string;
    definition?: string;
}

interface InstructionFrontMatter {
    id?: string;
    name?: string;
    description?: string;
    when_to_use?: string[];
    switch_when?: string[];
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
const _roleUiCache = new Map<string, RoleUiConfig | Promise<RoleUiConfig>>();
const _systemPromptCache = new Map<string, { result: SystemPromptResult; timestamp: number } | Promise<SystemPromptResult>>();
const _instructionsCache = new Map<string, InstructionInfo[] | Promise<InstructionInfo[]>>();

const CACHE_TTL = 60 * 60 * 1000; // 1小时缓存过期时间（毫秒）
const MAX_CACHE_ENTRIES = 200;
const FETCH_TIMEOUT_SHORT_MS = 5000;
const FETCH_TIMEOUT_MEDIUM_MS = 8000;
const FETCH_TIMEOUT_LONG_MS = 12000;
const INSTRUCTION_ID_ALIASES: Record<string, string> = {
    interrogation: 'search',
};

function parseInstructionFrontMatter(rawText: string): { metadata: InstructionFrontMatter; body: string } {
    const text = String(rawText || '');
    if (!text.startsWith('---\n')) {
        return { metadata: {}, body: text };
    }

    const endMarkerIndex = text.indexOf('\n---\n', 4);
    if (endMarkerIndex === -1) {
        return { metadata: {}, body: text };
    }

    const frontMatterText = text.slice(4, endMarkerIndex);
    const body = text.slice(endMarkerIndex + 5);

    try {
        const metadata = (yaml.load(frontMatterText) as InstructionFrontMatter) || {};
        return { metadata, body };
    } catch (error) {
        logger.warn('[PromptService] 解析行为 front matter 失败，将回退为纯正文:', error);
        return { metadata: {}, body: text };
    }
}

function formatBehaviorRoutingPrompt(
    instructions: Array<InstructionInfo & { metadata?: InstructionFrontMatter }>,
    currentInstructionId: string
): string {
    const lines = instructions.map(item => {
        const metadata = item.metadata || {};
        const visibleName = metadata.name || item.name || item.id;
        const header = `- ${item.id}: ${visibleName}`;
        const description = metadata.description ? `  说明: ${metadata.description}` : '';
        const whenToUse = Array.isArray(metadata.when_to_use) && metadata.when_to_use.length > 0
            ? `  什么时候用: ${metadata.when_to_use.join('；')}`
            : '';
        const switchWhen = Array.isArray(metadata.switch_when) && metadata.switch_when.length > 0
            ? `  何时切换: ${metadata.switch_when.join('；')}`
            : '';

        return [header, description, whenToUse, switchWhen].filter(Boolean).join('\n');
    });

    return `

# 行为目录

当前行为ID：
- ${currentInstructionId}

当前可用行为：
${lines.join('\n') || '- chat: ☕ 闲聊'}

切换原则：
- 命中行为文件头中的“什么时候用”，立刻调用 switch_behavior 切换
- 不要停留在当前行为里犹豫、试答、观望
- 当前行为与用户诉求不一致时，立刻切换到更匹配的行为
`;
}

function touchCacheEntry<T>(cache: Map<string, T>, key: string): T | undefined {
    const value = cache.get(key);
    if (value === undefined) return undefined;
    cache.delete(key);
    cache.set(key, value);
    return value;
}

function setCacheEntry<T>(cache: Map<string, T>, key: string, value: T): void {
    if (cache.has(key)) {
        cache.delete(key);
    }
    cache.set(key, value);
    while (cache.size > MAX_CACHE_ENTRIES) {
        const oldestKey = cache.keys().next().value as string | undefined;
        if (!oldestKey) break;
        cache.delete(oldestKey);
    }
}

function pruneExpiredSystemPromptCache(): void {
    const now = Date.now();
    for (const [key, value] of _systemPromptCache.entries()) {
        if (!(value instanceof Promise) && now - value.timestamp > CACHE_TTL) {
            _systemPromptCache.delete(key);
        }
    }
}

async function fetchWithTimeout(
    url: string,
    timeoutMs: number = FETCH_TIMEOUT_MEDIUM_MS
): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await fetch(url, { signal: controller.signal });
    } finally {
        clearTimeout(timeoutId);
    }
}

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

// --- File Structure Functions ---
async function getFileStructure(domain: string): Promise<string> {
    logger.log(`[PromptService] 开始获取文件结构，domain: ${domain}`);

    try {
        // 直接读取 catalog.json 文件获取完整的目录结构
        const catalogUrl = `/domains/${domain}/metadata/catalog.json`;
        const response = await fetchWithTimeout(catalogUrl, FETCH_TIMEOUT_LONG_MS);

        if (!response.ok) {
            throw new Error(`Failed to load catalog: ${response.status} ${response.statusText}`);
        }

        const rawCatalogData = await response.json();
        const catalogData = filePathService.normalizeCatalogTreeRoot(rawCatalogData, domain);
        logger.log(`[PromptService] catalog.json 内容:`, catalogData);

        // 递归格式化目录树
        const formattedTree = formatCatalogTree(catalogData);

        return formattedTree;
    } catch (error) {
        logger.error('[PromptService] 获取目录结构失败:', error);
        return '# 文件结构加载失败\n';
    }
}

function formatCatalogTree(catalog: any, prefix = '', isRoot = true, depth = 0): string {
    let result = '';

    // 限制深度，只显示前两级目录
    const maxDepth = 2;

    if (isRoot) {
        result = '# 目录结构\n\n';
    }

    const entries = Object.entries(catalog).sort(([a], [b]) => a.localeCompare(b));

    entries.forEach(([key, value], index) => {
        const isLast = index === entries.length - 1;
        const connector = isRoot ? '' : (isLast ? '└── ' : '├── ');
        const newPrefix = isRoot ? '' : (isLast ? '    ' : '│   ');

        if (typeof value === 'object' && value !== null && depth < maxDepth) {
            // 这是一个目录，且深度在限制范围内
            result += `${prefix}${connector}${key}/\n`;
            result += formatCatalogTree(value, prefix + newPrefix, false, depth + 1);
        } else if (typeof value === 'object' && value !== null && depth >= maxDepth) {
            // 目录太深，只统计文件数量
            const fileCount = Object.values(value).filter(v =>
                typeof v === 'string' || (typeof v === 'object' && v !== null)
            ).length;
            result += `${prefix}${connector}${key}/ (包含 ${fileCount} 个文件)\n`;
        } else if (typeof value === 'string' || key.endsWith('.md')) {
            // 这是一个文件
            if (depth < maxDepth) {
                result += `${prefix}${connector}${key}\n`;
            }
        }
    });

    return result;
}

function buildDirectoryTree(items: any[]): DirectoryNode {
    const root: DirectoryNode = {
        name: '',
        isDirectory: true,
        children: []
    };

    // Sort items for consistent ordering
    const sortedItems = [...items].sort((a, b) => {
        const aParts = a.path.split('/');
        const bParts = b.path.split('/');

        // Compare parent directories first
        const minLen = Math.min(aParts.length, bParts.length);
        for (let i = 0; i < minLen - 1; i++) {
            if (aParts[i] !== bParts[i]) {
                return aParts[i].localeCompare(bParts[i]);
            }
        }

        // If same parent, directories come before files
        if (aParts.length !== bParts.length) {
            return aParts.length - bParts.length;
        }

        // Same depth, compare names
        return aParts[aParts.length - 1].localeCompare(bParts[bParts.length - 1]);
    });

    for (const item of sortedItems) {
        const parts = item.path.split('/').filter((p: string) => p);
        let current = root;

        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            const isLast = i === parts.length - 1;

            let child = current.children?.find((c: any) => c.name === part);
            if (!child) {
                child = {
                    name: part,
                    isDirectory: !isLast || !part.endsWith('.md'),
                    children: []
                };
                if (!current.children) {
                    current.children = [];
                }
                current.children.push(child);
            }

            current = child;
        }
    }

    return root;
}

function formatDirectoryTree(tree: DirectoryNode, prefix = '', isLast = true): string {
    if (!tree.name && tree.children) {
        // Root node - just format children
        return tree.children.map((child, index) => {
            const isChildLast = index === tree.children!.length - 1;
            return formatDirectoryTree(child, '', isChildLast);
        }).join('');
    }

    let result = '';
    const connector = isLast ? '└── ' : '├── ';

    result += `${prefix}${connector}${tree.name}${tree.isDirectory ? '/' : ''}\n`;

    if (tree.children && tree.children.length > 0) {
        const children = [...tree.children].sort((a, b) => {
            // Directories first, then files
            if (a.isDirectory !== b.isDirectory) {
                return b.isDirectory ? 1 : -1;
            }
            return a.name.localeCompare(b.name);
        });

        const newPrefix = prefix + (isLast ? '    ' : '│   ');

        children.forEach((child, index) => {
            const isChildLast = index === children.length - 1;
            result += formatDirectoryTree(child, newPrefix, isChildLast);
        });
    }

    return result;
}

async function buildEmoteProtocolPrompt(v: number, roleId?: string): Promise<string> {
    const fallbackDescriptions: Record<string, string> = {
        happy: '开心、积极、成功、欢迎',
        sad: '伤心、歉意、遗憾、失落',
        angry: '生气、抱怨、批评、反对',
        surprised: '惊讶、意外、震惊',
        confused: '困惑、不理解、疑惑',
        shy: '害羞、收到赞美、不好意思',
        meow: '卖萌、撒娇、可爱',
        baka: '吐槽、轻微责备、笨蛋',
        sigh: '无奈、感慨、叹气',
        cpu: '思考中、处理中、计算',
        like: '喜欢、赞同、点赞',
        work: '工作、努力、认真',
        sleep: '疲劳、困倦、休息',
        morning: '早安、问候、起床',
        see: '看到、注视、发现',
        reply: '回复、应答、响应',
        fool: '傻傻的、搞笑、滑稽',
        givemoney: '求打赏、撒钱、金币',
        color: '脸红、害羞、尴尬',
    };

    let descriptions = fallbackDescriptions;
    try {
        const resp = await fetchWithTimeout(`/meme/memes_data.json?v=${v}`, FETCH_TIMEOUT_SHORT_MS);
        if (resp.ok) {
            const data = await resp.json();
            if (data && typeof data === 'object' && !Array.isArray(data)) {
                descriptions = data as Record<string, string>;
            }
        }
    } catch (error) {
        logger.warn('[PromptService] 无法加载 memes_data.json，使用内置描述:', error);
    }

    const isCustomPersona = Boolean(roleId && roleId.startsWith('custom_persona_'));
    let availableEmoteNames = new Set<string>();
    let hasIndexData = false;

    try {
        const indexResp = await fetchWithTimeout(`/meme/meme_index.json?v=${v}`, FETCH_TIMEOUT_SHORT_MS);
        if (indexResp.ok) {
            hasIndexData = true;
            const indexData = await indexResp.json() as {
                default?: Record<string, string[]>;
                agents?: Record<string, Record<string, string[]>>;
            };

            if (roleId && !isCustomPersona) {
                const roleMap = indexData.agents?.[roleId] || {};
                availableEmoteNames = new Set(
                    Object.entries(roleMap)
                        .filter(([, files]) => Array.isArray(files) && files.length > 0)
                        .map(([name]) => name)
                );
            } else {
                const defaultMap = indexData.default || {};
                availableEmoteNames = new Set(
                    Object.entries(defaultMap)
                        .filter(([, files]) => Array.isArray(files) && files.length > 0)
                        .map(([name]) => name)
                );
            }
        }
    } catch (error) {
        logger.warn('[PromptService] 无法加载 meme_index.json，将禁用表情输出:', error);
    }

    // 安全策略：
    // - 内置角色：索引异常时禁用表情，避免提示词与真实资源不一致
    // - 自定义角色：索引异常时同样禁用表情，确保行为可预期
    if (!hasIndexData) {
        availableEmoteNames = new Set();
    }

    const filteredDescriptions = Object.entries(descriptions)
        .filter(([name]) => availableEmoteNames.has(name));

    const rows = filteredDescriptions
        .map(([name, desc]) => `| :${name}: | ${String(desc).replace(/\n/g, ' ').trim()} |`)
        .join('\n');

    const emoteRuleExtra = filteredDescriptions.length === 0
        ? '\n- 当前角色没有可用表情，禁止输出任何 :表情名:'
        : '';

    return `

## 表情语法

使用 :表情名: 格式表达情绪。**每次回复只能使用一个表情，且只能使用下表中的表情：**

| 表情 | 适用场景 |
|------|----------|
${rows}

**重要规则：**
- 每次回复最多使用一个表情
- 禁止使用上表之外的表情名称（如 :think:、:smile:、:cry: 等都是无效的）
${emoteRuleExtra}
`;
}

// --- Custom Instructions Management ---

function getCustomInstructions(): InstructionInfo[] {
    try {
        return storageFacade.getCustomInstructions<InstructionInfo[]>();
    } catch (error) {
        logger.error('[PromptService] 从 LocalStorage 加载自定义指令失败:', error);
        return [];
    }
}

function saveCustomInstructions(customInstructions: InstructionInfo[]): void {
    try {
        storageFacade.setCustomInstructions(customInstructions);
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
    _systemPromptCache.clear();

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
    _systemPromptCache.clear();

    logger.log(`[PromptService] 已删除自定义指令: "${removedInstruction.name}"`);
    return true;
}

// --- Custom Personas Management ---

function getCustomPersonas(): CustomPersona[] {
    try {
        return storageFacade.getCustomPersonas<CustomPersona[]>();
    } catch (error) {
        logger.error('[PromptService] 从 LocalStorage 加载自定义角色失败:', error);
        return [];
    }
}

function saveCustomPersonas(customPersonas: CustomPersona[]): void {
    try {
        storageFacade.setCustomPersonas(customPersonas);
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
    const cached = touchCacheEntry(_instructionsCache, cacheKey);

    if (cached && !(cached instanceof Promise)) return cached;
    if (cached instanceof Promise) return cached;

    const loadPromise = (async () => {
        try {
            // Fetch static instructions
            const v = Date.now();
            const response = await fetchWithTimeout(`/prompts/agent/instructions.json?v=${v}`, FETCH_TIMEOUT_MEDIUM_MS);
            if (!response.ok) throw new Error('无法加载指令列表');
            const staticInstructions = await response.json() as InstructionInfo[];

            // Get custom instructions
            const customInstructions = getCustomInstructions();

            // Combine and cache
            const allInstructions = [...customInstructions, ...staticInstructions];
            setCacheEntry(_instructionsCache, cacheKey, allInstructions);
            return allInstructions;
        } catch (error) {
            logger.error('[PromptService] 加载指令列表失败:', error);
            _instructionsCache.delete(cacheKey);
            // Fallback to custom instructions only
            return getCustomInstructions();
        }
    })();

    setCacheEntry(_instructionsCache, cacheKey, loadPromise);
    return loadPromise;
}

function resolveInstructionById(
    instructions: InstructionInfo[],
    requestedId: string
): InstructionInfo | undefined {
    const direct = instructions.find(item => item.id === requestedId);
    if (direct) return direct;

    const aliasTarget = INSTRUCTION_ID_ALIASES[requestedId];
    if (!aliasTarget) return undefined;

    return instructions.find(item => item.id === aliasTarget);
}

async function _fetchAgentName(domain: string, roleId: string): Promise<string> {
    // 验证输入参数，防止缓存键冲突
    if (!domain || !roleId) {
        logger.error("[PromptService] _fetchAgentName: 缺少必要参数", { domain, roleId });
        return '参数错误';
    }

    const cacheKey = `${domain}|${roleId}`; // 使用更安全的分隔符
    const cached = touchCacheEntry(_agentNameCache, cacheKey);

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
            const roleConfigResponse = await fetchWithTimeout(`${roleConfigPath}?v=${v}`, FETCH_TIMEOUT_MEDIUM_MS);
            if (!roleConfigResponse.ok) return '未知角色';

            const roleConfig = yaml.load(await roleConfigResponse.text()) as RoleConfig;
            const personaPath = roleConfig?.customModes?.[0]?.persona;
            if (!personaPath) return '配置错误';

            const finalPersonaPath = resolvePath(roleConfigPath, personaPath);
            const personaResponse = await fetchWithTimeout(`${finalPersonaPath}?v=${v}`, FETCH_TIMEOUT_MEDIUM_MS);
            if (!personaResponse.ok) return '无名氏';

            const personaConfig = yaml.load(await personaResponse.text()) as PersonaConfig;
            const agentName = personaConfig?.name || 'AI';

            // 将结果存入缓存，替换 Promise
            setCacheEntry(_agentNameCache, cacheKey, agentName);
            return agentName;
        } catch (error) {
            // 发生错误时，从缓存中移除该 Promise
            _agentNameCache.delete(cacheKey);
            logger.error(`[PromptService] _fetchAgentName for '${roleId}' 失败:`, error);
            return '加载失败';
        }
    })();

    // 将 Promise 存入缓存
    setCacheEntry(_agentNameCache, cacheKey, loadPromise);

    return loadPromise;
}

async function _fetchRoleUi(domain: string, roleId: string): Promise<RoleUiConfig> {
    if (!domain || !roleId) {
        return {};
    }

    const cacheKey = `${domain}|${roleId}`;
    const cached = touchCacheEntry(_roleUiCache, cacheKey);

    if (cached && !(cached instanceof Promise)) {
        return cached;
    }

    if (cached instanceof Promise) {
        try {
            return await cached;
        } catch {
            _roleUiCache.delete(cacheKey);
        }
    }

    const loadPromise = (async () => {
        try {
            const v = Date.now();
            const roleConfigPath = `/domains/${domain}/core/roles/${roleId}.yaml`;
            const roleConfigResponse = await fetchWithTimeout(`${roleConfigPath}?v=${v}`, FETCH_TIMEOUT_MEDIUM_MS);
            if (!roleConfigResponse.ok) {
                setCacheEntry(_roleUiCache, cacheKey, {});
                return {};
            }

            const roleConfig = yaml.load(await roleConfigResponse.text()) as RoleConfig;
            const ui = roleConfig?.ui || {};
            setCacheEntry(_roleUiCache, cacheKey, ui);
            return ui;
        } catch (error) {
            _roleUiCache.delete(cacheKey);
            logger.warn(`[PromptService] _fetchRoleUi for '${roleId}' 失败:`, error);
            return {};
        }
    })();

    setCacheEntry(_roleUiCache, cacheKey, loadPromise);
    return loadPromise;
}

async function listAvailableAgents(domain: string): Promise<AgentInfo[]> {
    try {
        const v = Date.now();
        const manifestPath = `/domains/${domain}/core/roles.json?v=${v}`;
        const response = await fetchWithTimeout(manifestPath, FETCH_TIMEOUT_MEDIUM_MS);

        if (!response.ok) throw new Error(`无法加载 agent 清单: ${response.statusText}`);

        const roleInfos: RoleInfo[] = await response.json();

        const agentsWithNames = await Promise.all(
            roleInfos.map(async (info) => {
                const name = await _fetchAgentName(domain, info.id);
                const ui = await _fetchRoleUi(domain, info.id);
                return {
                    ...info,
                    name,
                    icon: ui.icon,
                    memePack: ui.memePack,
                };
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

    pruneExpiredSystemPromptCache();
    const cacheKey = `${domain}|${roleId}|${instructionId}`; // 增加指令ID到缓存键
    const cached = touchCacheEntry(_systemPromptCache, cacheKey);

    // 检查缓存是否过期
    let isExpired = false;
    if (cached && !(cached instanceof Promise)) {
        isExpired = Date.now() - cached.timestamp > CACHE_TTL;
    }

    // 如果缓存中已有未过期的结果，直接返回
    if (cached && !(cached instanceof Promise) && !isExpired) {
        return cached.result;
    }
    if (cached && !(cached instanceof Promise) && isExpired) {
        _systemPromptCache.delete(cacheKey);
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

                const roleConfigResponse = await fetchWithTimeout(`${roleConfigPath}?v=${v}`, FETCH_TIMEOUT_MEDIUM_MS);
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

                const personaResponse = await fetchWithTimeout(`${finalPersonaPath}?v=${v}`, FETCH_TIMEOUT_MEDIUM_MS);
                if (!personaResponse.ok) throw new Error(`无法加载 Persona 模块: ${personaResponse.statusText}`);

                const personaText = await personaResponse.text();
                const personaConfig = yaml.load(personaText) as PersonaConfig;
                personaDefinition = personaConfig?.definition || '';
                agentName = personaConfig?.name || 'AI';
            }

            // 获取指令
            const instructionsList = await listAvailableInstructions();
            const instruction = resolveInstructionById(instructionsList, instructionId)
                || resolveInstructionById(instructionsList, 'chat');
            const resolvedInstructionId = instruction?.id || 'chat';

            let instructionsPrompt = '';
            const instructionsWithMetadata: Array<InstructionInfo & { metadata?: InstructionFrontMatter }> = [];
            for (const item of instructionsList) {
                if (item.isCustom && item.content) {
                    const parsed = parseInstructionFrontMatter(item.content);
                    instructionsWithMetadata.push({
                        ...item,
                        content: parsed.body,
                        metadata: parsed.metadata,
                    });
                    continue;
                }

                if (item.path) {
                    try {
                        const instructionPath = `/prompts/agent/${item.path}`;
                        const instructionResponse = await fetchWithTimeout(`${instructionPath}?v=${v}`, FETCH_TIMEOUT_LONG_MS);
                        if (!instructionResponse.ok) {
                            instructionsWithMetadata.push(item);
                            continue;
                        }
                        const rawInstructionText = await instructionResponse.text();
                        const parsed = parseInstructionFrontMatter(rawInstructionText);
                        instructionsWithMetadata.push({
                            ...item,
                            content: parsed.body,
                            metadata: parsed.metadata,
                        });
                    } catch (error) {
                        logger.warn(`[PromptService] 读取行为元数据失败: ${item.id}`, error);
                        instructionsWithMetadata.push(item);
                    }
                    continue;
                }

                instructionsWithMetadata.push(item);
            }

            let activeInstructionRecord = instructionsWithMetadata.find(item => item.id === instruction?.id);
            if (!activeInstructionRecord && instruction) {
                activeInstructionRecord = {
                    ...instruction,
                    metadata: {},
                };
            }
            if (instruction) {
                if (activeInstructionRecord?.isCustom && activeInstructionRecord.content) {
                    // It's a custom instruction, use its content directly
                    instructionsPrompt = activeInstructionRecord.content;
                } else if (activeInstructionRecord?.content) {
                    instructionsPrompt = activeInstructionRecord.content;
                } else if (instruction.path) {
                    // It's a static instruction, fetch from file
                    const instructionPath = `/prompts/agent/${instruction.path}`;
                    const instructionsResponse = await fetchWithTimeout(`${instructionPath}?v=${v}`, FETCH_TIMEOUT_LONG_MS);
                    if (!instructionsResponse.ok) throw new Error(`无法加载 Instructions 模块: ${instructionsResponse.statusText}`);
                    const rawInstructionText = await instructionsResponse.text();
                    instructionsPrompt = parseInstructionFrontMatter(rawInstructionText).body;
                }
            }

            if (!instructionsPrompt) {
                // Fallback to default chat.md if instruction was not found or failed to load
                const fallbackInstructionPath = `/prompts/agent/chat.md`;
                const fallbackResponse = await fetchWithTimeout(`${fallbackInstructionPath}?v=${v}`, FETCH_TIMEOUT_LONG_MS);
                if (!fallbackResponse.ok) throw new Error(`无法加载默认指令模块: ${fallbackResponse.statusText}`);
                instructionsPrompt = parseInstructionFrontMatter(await fallbackResponse.text()).body;
            }

            const behaviorCatalogPrompt = formatBehaviorRoutingPrompt(instructionsWithMetadata, resolvedInstructionId);

            // 加载系统指令
            let systemDirectivePrompt = '';
            try {
                const systemDirectiveResponse = await fetchWithTimeout(`/prompts/system_directive.md?v=${v}`, FETCH_TIMEOUT_LONG_MS);
                if (systemDirectiveResponse.ok) {
                    systemDirectivePrompt = await systemDirectiveResponse.text();
                    systemDirectivePrompt = `\n\n${systemDirectivePrompt}`;
                }
            } catch (error) {
                logger.warn('[PromptService] 无法加载系统指令:', error);
            }

            // 加载工具使用总指令（何时/如何/怎么使用工具）
            let toolUsageDirectivePrompt = '';
            try {
                const toolUsageDirectiveResponse = await fetchWithTimeout(`/prompts/tool_usage_directive.md?v=${v}`, FETCH_TIMEOUT_LONG_MS);
                if (toolUsageDirectiveResponse.ok) {
                    toolUsageDirectivePrompt = await toolUsageDirectiveResponse.text();
                    toolUsageDirectivePrompt = `\n\n${toolUsageDirectivePrompt}`;
                }
            } catch (error) {
                logger.warn('[PromptService] 无法加载工具使用总指令:', error);
            }

            let memoryPolicyPrompt = '';
            try {
                const memoryPolicyResponse = await fetchWithTimeout(`/prompts/agent/memory_policy.md?v=${v}`, FETCH_TIMEOUT_LONG_MS);
                if (memoryPolicyResponse.ok) {
                    memoryPolicyPrompt = await memoryPolicyResponse.text();
                    memoryPolicyPrompt = `\n\n${memoryPolicyPrompt}`;
                }
            } catch (error) {
                logger.warn('[PromptService] 无法加载记忆策略提示词:', error);
            }

            // 注入执行型工具提示词（已在注册层过滤掉 UI 协议工具），
            // 同时保留 ask_choice 的 UI 协议语法说明。
            await toolPromptService.loadToolPrompts();
            const toolsPrompt = toolPromptService.getSystemPrompt();

            const emoteProtocolPrompt = await buildEmoteProtocolPrompt(v, roleId);

            const uiProtocolPrompt = `

# UI 协议指令

${emoteProtocolPrompt}

## 提问语法

当需要用户做选择时，使用 [?问题|选项1|选项2] 格式：
[?你想了解什么内容|角色背景|技能介绍|剧情故事]

规则：
- 最少2个选项，最多4个选项
- 选项用 | 分隔
- 每个选项简短明了（不超过10字）

## 组合示例
:happy: 很高兴见到你！[?你想聊什么|闲聊|查资料]
`;

            const finalSystemPrompt = `${systemDirectivePrompt}${toolUsageDirectivePrompt}${toolsPrompt}${memoryPolicyPrompt}${uiProtocolPrompt}\n\n${personaDefinition}\n\n${instructionsPrompt}${behaviorCatalogPrompt}`;

            const result = {
                systemPrompt: finalSystemPrompt,
                agentName: agentName
            };

            // 将结果和时间戳存入缓存，替换 Promise
            setCacheEntry(_systemPromptCache, cacheKey, { result, timestamp: Date.now() });
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
    setCacheEntry(_systemPromptCache, cacheKey, loadPromise);

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
