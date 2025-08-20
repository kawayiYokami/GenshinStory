import { ref, Ref, watch } from 'vue';
import { renderMarkdownSync, replaceLinkPlaceholders } from '@/features/viewer/services/MarkdownRenderingService';

/**
 * 智能缓冲 Composable 函数
 * @param contentRef - 包含原始内容的 ref
 * @param streamCompletedRef - 表示流是否完成的 ref
 * @returns 包含渲染 HTML 的 ref
 */
export function useSmartBuffer(
  contentRef: Ref<string>,
  streamCompletedRef: Ref<boolean>
) {
  // 状态变量
  const renderableContent = ref('');
  const buffer = ref<string[]>([]); // 使用数组而不是字符串来优化性能
  const isBuffering = ref(false);
  const expectedClosingTag = ref<string | null>(null);
  const renderedHtml = ref('');

  // 检查是否在代码块内
  const isInCodeBlock = (content: string) => {
    // 简单检查是否有未闭合的代码块标记
    const codeBlockCount = (content.match(/```/g) || []).length;
    return codeBlockCount % 2 !== 0 || content.includes('```');
  };

  // 核心缓冲逻辑：监听 contentRef 的变化
  watch(contentRef, (newContent) => {
    if (typeof newContent !== 'string' || !newContent) {
      renderableContent.value = '';
      return;
    }

    // 如果在代码块内，禁用缓冲，直接更新渲染内容
    if (isInCodeBlock(newContent)) {
      renderableContent.value = newContent;
      return;
    }

    // 如果不处于缓冲状态
    if (!isBuffering.value) {
      // 检测是否有触发缓冲的起始标记（如 <tool>）
      const toolStartIndex = newContent.indexOf('<tool>');
      
      if (toolStartIndex !== -1) {
        // 进入缓冲状态
        isBuffering.value = true;
        expectedClosingTag.value = '</tool>';
        
        // 将标记前的内容更新到 renderableContent
        renderableContent.value = newContent.substring(0, toolStartIndex);
        
        // 将标记后的内容存入 buffer 数组
        buffer.value = [newContent.substring(toolStartIndex)];
      } else {
        // 没有检测到起始标记，直接更新 renderableContent
        renderableContent.value = newContent;
      }
    } else {
      // 正处于缓冲状态，将新文本追加到 buffer 数组中
      const newContentPart = newContent.slice(renderableContent.value.length + buffer.value.join('').length);
      if (newContentPart) {
        buffer.value.push(newContentPart);
      }
      
      // 检查 buffer 是否已包含 expectedClosingTag
      if (buffer.value.join('').includes(expectedClosingTag.value || '')) {
        // 将 buffer 内容合并到 renderableContent
        renderableContent.value += buffer.value.join('');
        
        // 退出缓冲状态
        isBuffering.value = false;
        buffer.value = [];
        expectedClosingTag.value = null;
      }
    }
  });

  // 智能容错逻辑：监听 streamCompletedRef 属性
  watch(streamCompletedRef, (newStreamCompleted, oldStreamCompleted) => {
    // 检测到流从"进行中"变为"已结束"
    if (oldStreamCompleted === false && newStreamCompleted === true) {
      // 检查是否仍处于缓冲状态
      if (isBuffering.value) {
        // 强制清空缓冲区
        const bufferContent = buffer.value.join('');
        
        // 检查 buffer 内容是否包含 expectedClosingTag
        if (expectedClosingTag.value && !bufferContent.includes(expectedClosingTag.value)) {
          // 自动补全闭合标签
          buffer.value.push(expectedClosingTag.value);
        }
        
        // 将处理后的缓冲区内容合并到 renderableContent
        renderableContent.value += buffer.value.join('');
        
        // 退出缓冲状态
        isBuffering.value = false;
        buffer.value = [];
        expectedClosingTag.value = null;
      }
    }
  });

  // 始终基于 renderableContent 的变化来更新最终的 renderedHtml
  watch(() => renderableContent.value, async (newRenderableContent) => {
    if (typeof newRenderableContent !== 'string') {
      renderedHtml.value = '';
      return;
    }

    const rendered = renderMarkdownSync(newRenderableContent);
    const finalHtml = await replaceLinkPlaceholders(rendered);
    renderedHtml.value = finalHtml;
  });

  return {
    renderableContent,
    renderedHtml,
    isBuffering,
    buffer,
    expectedClosingTag
  };
}