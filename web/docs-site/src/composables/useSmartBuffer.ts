import { ref, watch } from 'vue';
import type { Ref } from 'vue';
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

  // 初始化时就设置 renderableContent
  if (contentRef.value) {
    renderableContent.value = contentRef.value;
  }

  // 核心缓冲逻辑：监听 contentRef 的变化
  watch(contentRef, (newContent) => {
    if (typeof newContent !== 'string' || !newContent) {
      renderableContent.value = '';
      return;
    }

    // 如果不处于缓冲状态
    if (!isBuffering.value) {
      // 检测到 { 就立即截断，等待流结束后一次性显示
      const braceIndex = newContent.indexOf('{');
      if (braceIndex !== -1) {
        // 截断内容，忽略 { 及之后的所有内容
        renderableContent.value = newContent.substring(0, braceIndex);

        // 进入缓冲状态，但忽略后续所有内容
        isBuffering.value = true;
        expectedClosingTag.value = null; // 不需要特定的闭合标记

        return;
      }

      // 没有检测到起始标记，直接更新 renderableContent
      renderableContent.value = newContent;
    } else {
      // 正处于缓冲状态
      if (expectedClosingTag.value === null) {
        // 如果是因为检测到 { 而进入缓冲状态，则忽略所有新内容
        // 不做任何处理，等待流结束
        return;
      } else {
        // 原有的缓冲逻辑（处理其他类型的缓冲）
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
    }
  });

  // 智能容错逻辑：监听 streamCompletedRef 属性
  watch(streamCompletedRef, (newStreamCompleted, oldStreamCompleted) => {
    // 检测到流从"进行中"变为"已结束"
    if (oldStreamCompleted === false && newStreamCompleted === true) {
      // 检查是否仍处于缓冲状态
      if (isBuffering.value) {
        // 如果是因为检测到 { 而进入缓冲状态，则忽略所有缓冲内容
        if (expectedClosingTag.value === null) {
          // 退出缓冲状态，不添加任何内容
          isBuffering.value = false;
          buffer.value = [];
        } else {
          // 原有的缓冲逻辑（处理其他类型的缓冲）
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
  }, { immediate: true }); // 添加 immediate: true 确保初始化时就执行

  return {
    renderableContent,
    renderedHtml,
    isBuffering,
    buffer,
    expectedClosingTag
  };
}
