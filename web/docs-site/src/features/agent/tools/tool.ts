// web/docs-site/src/features/agent/tools/tool.ts

// 定义工具执行的返回结果结构
export interface ToolExecutionResult {
  // 工具执行后返回给用户的可见内容
  result: string;
  // 可选的、一次性的后续提示，将作为隐藏的用户消息注入对话历史
  followUpPrompt?: string;
}

export interface Tool<P = any> {
  name: string;
  type: 'ui' | 'execution';
  description: string;
  usage: string;
  examples: string[];
  error_guidance: string;

  // 工具的执行逻辑，返回一个包含结果和可选后续提示的对象
  execute(params: P): Promise<ToolExecutionResult>;
}