<template>
  <div class="card card-compact bg-base-100 border border-base-300 shadow-xs rounded-2xl" ref="toolResultCard">
    <div class="card-body p-0">
      <div class="collapse collapse-arrow rounded-2xl ">
        <input type="checkbox" />
        <div class="collapse-title p-0 min-h-0">
          <div class="tool-result-card items-center">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-success shrink-0">
              <Info class="h-4 w-4 text-base-content" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-base-content">检索结果</div>
              <div class="text-xs opacity-70 truncate">{{ searchQuery }}</div>
            </div>
          </div>
        </div>
        <div class="collapse-content ">
          <div class="pt-0 p-0">
            <div v-if="parsedResults.length > 0" class="search-results-list">
              <div class="flex items-center justify-between mb-2 px-1">
                <span class="text-xs font-bold text-base-content/50 uppercase tracking-wider">
                  找到 {{ isGrouped ? totalFiles : parsedResults.length }} 个相关结果
                </span>
              </div>
              <div class="space-y-2">
                <!-- 分组模式显示 -->
                <template v-if="isGrouped">
                  <div
                    v-for="(group, index) in parsedResults"
                    :key="index"
                    class="search-result-group border border-base-200 rounded-xl bg-base-100"
                  >
                    <!-- 文件标题 -->
                    <button
                      class="search-result-item internal-doc-link w-full text-left group relative p-3 rounded-t-xl hover:bg-base-200 transition-colors"
                      :data-path="group.path || ''"
                      :data-raw-link="`[[${group.title || extractFileName(group.path || '')}|path:${group.path || ''}]]`"
                      @click="handleLinkClick"
                    >
                      <div class="flex items-start justify-between gap-3 w-full">
                        <div class="flex items-center gap-2 min-w-0">
                          <span class="font-semibold text-sm text-base-content group-hover:text-accent-content transition-colors truncate">
                            {{ group.title || extractFileName(group.path || '') }}
                          </span>
                        </div>
                        <div class="flex items-center gap-2 shrink-0">
                          <span class="badge badge-sm badge-primary font-mono text-[10px]">
                            {{ (isGroupedResult(group) ? group.hitCount : 0) }} 处命中
                          </span>
                        </div>
                      </div>
                      <div class="flex items-center gap-1.5 px-1 mt-0.5 w-full">
                        <span class="text-[10px] text-base-content/40 truncate font-mono">{{ group.path }}</span>
                      </div>
                    </button>

                    <!-- 命中详情 -->
                    <div class="border-t border-base-200 px-3 pb-3 pt-2">
                      <div class="space-y-2">
                        <div
                          v-for="(hit, hitIndex) in isGroupedResult(group) ? group.hits : []"
                          :key="hitIndex"
                          class="search-result-item internal-doc-link relative pl-3 text-left group"
                          :data-path="group.path || ''"
                          :data-raw-link="`[[${group.title || extractFileName(group.path || '')}|path:${group.path || ''}:${hit.line}]]`"
                          :data-snippet="hit.snippet.replace(/^>\\s*/, '').replace(/\\.\\.\\.$/, '')"
                          @click="handleLinkClick"
                        >
                          <div class="absolute left-0 top-2 bottom-2 w-0.5 bg-base-300 group-hover:bg-accent-content transition-colors rounded-full"></div>
                          <div class="flex items-center gap-2 mb-1">
                            <span class="badge badge-sm badge-ghost shrink-0 font-mono text-[10px] opacity-70">
                              Ln {{ hit.line }}
                            </span>
                          </div>
                          <div class="text-xs text-base-content/70 leading-relaxed font-mono">
                            {{ hit.snippet }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>

                <!-- 原始非分组模式 -->
                <template v-else>
                  <button
                    v-for="(item, index) in parsedResults"
                    :key="index"
                    class="search-result-item internal-doc-link w-full text-left group relative flex flex-col gap-2 p-3 rounded-xl bg-base-300 border border-base-200 hover:border-primary/30 hover:shadow-sm transition-all duration-200"
                    :data-path="item.path || ''"
                    :data-raw-link="`[[${item.title || extractFileName(item.path || '')}|path:${item.path || ''}${(item as SearchResult).line ? ':' + (item as SearchResult).line : ''}]]`"
                    @click="handleLinkClick"
                  >
                    <!-- 标题行 -->
                    <div class="flex items-start justify-between gap-3 w-full">
                      <div class="flex items-center gap-2 min-w-0">
                        <span
                          class="font-semibold text-sm text-base-content group-hover:text-accent-content transition-colors truncate"
                        >
                          {{ item.title || extractFileName(item.path || '') }}
                        </span>
                      </div>
                      <div v-if="(item as SearchResult).line" class="badge badge-sm badge-ghost shrink-0 font-mono text-[10px] opacity-70">
                        Ln {{ (item as SearchResult).line }}
                      </div>
                    </div>

                    <!-- 摘要 -->
                    <div v-if="(item as SearchResult).snippet" class="relative pl-3 w-full">
                      <div class="absolute left-0 top-1 bottom-1 w-0.5 bg-base-300 group-hover:bg-accent-content transition-colors rounded-full"></div>
                      <div class="text-xs text-base-content/70 line-clamp-2 leading-relaxed font-mono">
                        {{ (item as SearchResult).snippet }}
                      </div>
                    </div>

                    <!-- 路径 -->
                    <div class="flex items-center gap-1.5 px-1 mt-0.5 w-full">
                      <span class="text-[10px] text-base-content/40 truncate font-mono">{{ item.path }}</span>
                    </div>
                  </button>
                </template>
              </div>
            </div>

            <!-- 原始内容作为后备 -->
            <div v-if="!hasValidResults" class="mt-2">
              <div class="text-xs font-bold text-base-content/50 uppercase tracking-wider mb-2">原始响应内容</div>
              <pre class="whitespace-pre-wrap break-all font-mono text-xs bg-base-100 border border-base-200 p-3 rounded-xl text-base-content/80">{{ formattedContent }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { Info, ExternalLink } from 'lucide-vue-next';
import { processSingleLinkText } from '@/features/viewer/services/MarkdownRenderingService';
import { extractFileName } from '@/utils/pathUtils';
import { useDocumentViewerStore } from '@/features/app/stores/documentViewer';
import linkProcessorService from '@/lib/linkProcessor/linkProcessorService';
import type { LinkResolutionResult } from '@/lib/linkProcessor/linkProcessorService';

interface SearchResult {
  path?: string;
  line?: number;
  snippet?: string;
  totalLines?: number;
  totalTokens?: number;
  title?: string;
}

interface GroupedSearchResult {
  path?: string;
  title?: string;
  totalLines?: number;
  totalTokens?: number;
  hits?: Array<{
    line: number;
    snippet: string;
  }>;
  hitCount?: number;
}

interface Props {
  content?: string;
}

const props = withDefaults(defineProps<Props>(), {
  content: ''
});

const toolResultCard = ref<HTMLElement | null>(null);

// 处理内部链接点击
const handleLinkClick = async (event: Event) => {
  const target = (event.target as HTMLElement).closest('.internal-doc-link') as HTMLElement | null;
  if (target && target.dataset.rawLink) {
    event.preventDefault();
    event.stopPropagation();

    const rawLink = target.dataset.rawLink;
    let snippet = target.dataset.snippet;

    // 清理摘要格式
    if (snippet) {
      snippet = snippet.replace(/^>\s*/, '').replace(/\.\.\.$/, '');
    }

    if (rawLink) {
      try {
        const result: LinkResolutionResult = await linkProcessorService.resolveLink(rawLink);

        if (result.isValid && result.resolvedPath) {
          const docViewerStore = useDocumentViewerStore();
          // 不传递行号，只传递摘要作为关键词
          docViewerStore.open(result.resolvedPath, undefined, snippet ? [snippet] : undefined);
        } else {
          alert(`链接指向的路径 "${result.originalPath}" 无法被解析或找到。`);
        }
      } catch (error) {
        console.error('处理链接点击时出错:', error);
        alert(`链接处理失败: ${error}`);
      }
    }
  }
};

// 判断是否为分组结果的辅助函数
const isGroupedResult = (item: any): item is GroupedSearchResult => {
  return item && typeof item === 'object' && 'hits' in item && Array.isArray(item.hits);
};

// 组件挂载时添加事件监听
onMounted(() => {
  if (toolResultCard.value) {
    toolResultCard.value.addEventListener('click', handleLinkClick);
  }
});

// 组件卸载时清理事件监听
onUnmounted(() => {
  if (toolResultCard.value) {
    toolResultCard.value.removeEventListener('click', handleLinkClick);
  }
});

// 解析搜索结果 - 支持分组格式、新的平铺格式和旧格式
const parsedData = computed(() => {
  if (!props.content) return { query: '', results: [], grouped: false };

  try {
    // 尝试从内容中提取JSON部分
    let jsonStr = props.content;

    // 如果内容包含非JSON文本，尝试查找JSON对象
    const jsonMatch = props.content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonStr = jsonMatch[0];
    }

    const parsed = JSON.parse(jsonStr);

    // 新的平铺格式：{"tool": "search_docs", "query": "玛拉妮", "results": [...], "grouped": true}
    if (parsed.tool === 'search_docs') {
      return {
        query: parsed.query || '',
        results: parsed.results || [],
        grouped: parsed.grouped === true
      };
    }

    // 兼容旧格式：{"query": "...", "results": [...], "grouped": true}
    if (parsed.query && Array.isArray(parsed.results)) {
      return {
        query: parsed.query,
        results: parsed.results,
        grouped: parsed.grouped === true
      };
    } else if (parsed.docs && Array.isArray(parsed.docs)) {
      // 兼容旧文档列表格式：{"docs": [...]}
      return {
        query: '展开查看文档',
        results: parsed.docs,
        grouped: false
      };
    }
  } catch (error) {
    console.error('Failed to parse tool result:', error);
    console.log('Content that failed to parse:', props.content);
  }

  return { query: '', results: [], grouped: false };
});

const searchQuery = computed(() => parsedData.value.query);
const parsedResults = computed(() => parsedData.value.results as (SearchResult | GroupedSearchResult)[]);
const isGrouped = computed(() => parsedData.value.grouped);
const totalFiles = computed(() => parsedResults.value.length);
const hasValidResults = computed(() => parsedResults.value.length > 0);

// 格式化原始内容为后备显示
const formattedContent = computed(() => {
  try {
    // 尝试从内容中提取JSON部分
    let jsonStr = props.content;

    // 如果内容包含非JSON文本，尝试查找JSON对象
    const jsonMatch = props.content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonStr = jsonMatch[0];
    }

    const parsed = JSON.parse(jsonStr);
    return JSON.stringify(parsed, null, 2); // 格式化JSON
  } catch {
    return props.content;
  }
});

// 导航到文档（保留作为后备）
const navigateToDocument = (path?: string) => {
  if (!path) return;

  // 发送自定义事件给父组件处理导航
  const event = new CustomEvent('navigate-to-document', { detail: { path } });
  window.dispatchEvent(event);
};
</script>
