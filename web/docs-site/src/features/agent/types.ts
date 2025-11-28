/**
 * @fileoverview 代理系统类型定义文件
 * @description 定义智能代理系统中使用的所有接口和类型
 * @author yokami
 */

// --- 类型定义 ---

/**
 * 平铺工具调用接口
 * @description 定义扁平化的工具调用格式，替代嵌套的tool_call结构
 */
export interface FlatToolCall {
  /** 工具名称 */
  tool: 'search_docs' | 'read_doc' | 'ask';

  // 共用参数
  /** 路径参数 - search_docs: 搜索目录路径, read_doc: 读取文件路径 */
  path?: string;

  // search_docs 专用参数
  /** 搜索查询关键词 */
  query?: string;
  /** 搜索结果数量限制 */
  limit?: number;

  // read_doc 专用参数
  /** 读取目标描述 */
  target?: string;
  /** 行范围，格式如 "15-30" */
  line_range?: string;

  // ask 专用参数
  /** 问题文本 */
  question?: string;
  /** 建议选项列表 */
  suggestions?: string[];

  // 元数据字段
  /** 工具调用唯一ID */
  action_id?: string;
  /** 调用时间戳 */
  timestamp?: string;
  /** 执行结果 */
  result?: any;
  /** 执行状态 */
  status?: 'pending' | 'executing' | 'completed' | 'failed';
}

/**
 * 嵌套工具调用接口（向后兼容）
 * @description 保留原有的嵌套格式以维持向后兼容性
 */
export interface NestedToolCall {
  tool_call: {
    name: string;
    arguments: Record<string, any>;
  };
}

/**
 * 工具调用联合类型
 * @description 支持平铺和嵌套两种格式
 */
export type ToolCall = FlatToolCall | NestedToolCall;

/**
 * 格式检测辅助函数
 * @description 检测工具调用是否为平铺格式
 */
export function isFlatToolCall(tool: any): tool is FlatToolCall {
  return tool && typeof tool === 'object' && 'tool' in tool && !('tool_call' in tool);
}

/**
 * 格式转换辅助函数
 * @description 将嵌套格式转换为平铺格式
 */
export function convertToFlatToolCall(nestedTool: NestedToolCall): FlatToolCall {
  const { name, arguments: args } = nestedTool.tool_call;

  const flatTool: FlatToolCall = {
    tool: name as any,
    ...args
  };

  // 根据工具类型映射特定字段
  switch (name) {
    case 'search_docs':
      if (!flatTool.query && args.query) flatTool.query = args.query;
      break;
    case 'read_doc':
      if (!flatTool.target && args.target) flatTool.target = args.target;
      break;
    case 'ask':
      if (!flatTool.question && args.question) flatTool.question = args.question;
      if (args.suggestions && Array.isArray(args.suggestions)) {
        flatTool.suggestions = args.suggestions;
      }
      break;
  }

  return flatTool;
}

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
    /** 工具调用列表（支持平铺和嵌套格式） */
    tool_calls?: ToolCall[];
    /** 平铺工具调用列表（新增字段，优先使用） */
    tiled_tools?: FlatToolCall[];
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