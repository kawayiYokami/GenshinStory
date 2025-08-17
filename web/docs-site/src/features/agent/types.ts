// --- 类型定义 ---
export interface MessageContentPart {
    type: 'text' | 'image_url' | 'doc';
    text?: string;
    image_url?: { url: string };
    content?: string; // for doc
    name?: string; // for doc
    path?: string; // for doc
    error?: boolean; // for doc
}

export interface Message {
    id: string;
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string | MessageContentPart[];
    type?: 'text' | 'error' | 'tool_status' | 'tool_result' | 'system';
    status?: 'streaming' | 'done' | 'error' | 'rendering';
    streamCompleted?: boolean;
    is_hidden?: boolean;
    name?: string; // for tool role
    tool_calls?: any[];
    question?: {
        text: string;
        suggestions: string[];
    };
}

export interface Session {
    id: string;
    domain: string;
    roleId: string;
    name: string;
    createdAt: string;
    messagesById: { [key: string]: Message };
    messageIds: string[];
}

export interface AgentInfo {
    id: string;
    name: string;
    description: string;
}

export interface Command {
    type: 'CALL_AI' | 'EXECUTE_TOOL';
    payload?: any;
}