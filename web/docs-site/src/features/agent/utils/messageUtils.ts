
export interface ToolCall {
  original: string;
  tool: string;
  params: Record<string, any>;
}

/**
 * 清洗消息内容中的工具调用 JSON
 */
export function cleanContentFromToolCalls(content: string, toolCalls?: ToolCall[]): string {
  if (!toolCalls || toolCalls.length === 0) {
    return content;
  }

  let cleanedContent = content;

  // 直接使用 toolCall.original 进行替换，因为现在存储的是原始JSON
  for (const toolCall of toolCalls) {
    if (toolCall.original) {
      // 使用原始JSON进行精确替换
      cleanedContent = cleanedContent.replace(toolCall.original, '');
    }
  }

  // 移除 JSON 前后的换行符，但保留内容之间的换行
  cleanedContent = cleanedContent.replace(/\n\s*\n(?=\n*[^\n])/g, '\n');

  // 清理开头和结尾的空白
  cleanedContent = cleanedContent.trim();

  // 如果清洗后内容为空，返回空字符串
  if (!cleanedContent) {
    return '';
  }

  return cleanedContent;
}