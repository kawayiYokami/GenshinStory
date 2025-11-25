/**
 * @fileoverview 代理系统类型定义文件
 * @description 定义智能代理系统中使用的所有接口和类型
 * @author yokami
 */

// --- 类型定义 ---
/**
 * 消息内容部分接口
 * @description 定义消息内容的各个部分，支持文本、图片和文档类型
 */
export interface MessageContentPart {
    /** 内容类型 */
    type: 'text' | 'image_url' | 'doc';
    /** 文本内容 */
    text?: string;
    /** 图片URL */
    image_url?: { url: string };
    /** 文档内容（用于doc类型） */
    content?: string;
    /** 文档名称（用于doc类型） */
    name?: string;
    /** 文档路径（用于doc类型） */
    path?: string;
    /** 是否有错误（用于doc类型） */
    error?: boolean;
}

/**
 * 消息接口
 * @description 定义聊天消息的结构和属性
 */
export interface Message {
    /** 消息唯一标识符 */
    id: string;
    /** 消息角色 */
    role: 'system' | 'user' | 'assistant' | 'tool';
    /** 消息内容 */
    content: string | MessageContentPart[];
    /** 消息类型 */
    type?: 'text' | 'error' | 'tool_status' | 'tool_result' | 'system' | 'compression_summary';
    /** 消息状态 */
    status?: 'streaming' | 'done' | 'error' | 'rendering';
    /** 流是否完成 */
    streamCompleted?: boolean;
    /** 是否隐藏 */
    is_hidden?: boolean;
    /** 是否为压缩摘要消息 */
    isCompressed?: boolean;
    /** 工具名称（用于tool角色） */
    name?: string;
    /** 工具调用列表 */
    tool_calls?: any[];
    /** 问题建议（用于assistant角色） */
    question?: {
        /** 问题文本 */
        text: string;
        /** 建议列表 */
        suggestions: string[];
    };
    /** 创建时间 */
    createdAt: string;
}

/**
 * 会话接口
 * @description 定义聊天会话的结构和属性
 */
export interface Session {
    /** 会话唯一标识符 */
    id: string;
    /** 所属域名 */
    domain: string;
    /** 使用的角色ID */
    roleId: string;
    /** 会话名称 */
    name: string;
    /** 创建时间 */
    createdAt: string;
    /** 消息映射表 */
    messagesById: { [key: string]: Message };
    /** 消息ID列表 */
    messageIds: string[];
}

/**
 * 代理信息接口
 * @description 定义智能代理的基本信息
 */
export interface AgentInfo {
    /** 代理唯一标识符 */
    id: string;
    /** 代理名称 */
    name: string;
    /** 代理描述 */
    description: string;
}

/**
 * 命令接口
 * @description 定义代理系统中的命令结构
 */
export interface Command {
    /** 命令类型 */
    type: 'CALL_AI' | 'EXECUTE_TOOL';
    /** 命令负载 */
    payload?: any;
}