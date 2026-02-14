<template>
  <div class="card card-compact bg-base-100 border border-base-200 rounded-xl shadow-sm" ref="toolResultCard">
    <div class="collapse collapse-arrow p-0">
      <input type="checkbox" v-model="resultExpanded" />
      
      <!-- 极简单行标题 -->
      <div class="collapse-title min-h-0 py-2 px-3 flex items-center gap-2.5">
        <div class="flex h-6 w-6 items-center justify-center rounded-full shrink-0" :class="iconBgClass">
          <component :is="toolIcon" class="h-3.5 w-3.5 text-base-content" />
        </div>
        <div class="flex-1 min-w-0 flex items-center gap-1.5">
          <span class="text-sm font-medium text-base-content">{{ toolDisplayName }}</span>
          <span class="text-xs opacity-40">·</span>
          <span class="text-xs opacity-70 truncate">{{ compactSummary }}</span>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <span v-if="!isPending" class="text-xs opacity-60">{{ resultCountText }}</span>
          <span v-if="isPending" class="loading loading-spinner loading-xs"></span>
          <span v-else class="text-xs" :class="statusIconClass">{{ statusIcon }}</span>
        </div>
      </div>

      <!-- 展开的详细内容 -->
      <div class="collapse-content pt-0 px-3 pb-3">
        <div v-if="isPending" class="flex items-center gap-2 text-xs opacity-70 py-2">
          <span class="loading loading-spinner loading-xs"></span>
          <span>{{ pendingText }}</span>
        </div>

        <template v-else>
                              <!-- Explore 结果 -->
                              <div v-if="isExploreResult" class="pt-2 px-1">
                                <div class="flex flex-wrap gap-1.5 mb-2">
                                  <span v-if="expectedTaskCount !== null" class="badge badge-xs badge-ghost">计划 {{ expectedTaskCount }}</span>
                                  <span class="badge badge-xs badge-ghost">返回 {{ completedTaskCount }}</span>
                                  <span class="badge badge-xs badge-primary">调用 {{ totalUsedCalls }} 次</span>
                                  <span v-if="statusCounts.success > 0" class="badge badge-xs badge-success">成功 {{ statusCounts.success }}</span>
                                  <span v-if="statusCounts.partial > 0" class="badge badge-xs badge-warning">部分 {{ statusCounts.partial }}</span>
                                  <span v-if="statusCounts.failed > 0" class="badge badge-xs badge-error">失败 {{ statusCounts.failed }}</span>
                                  <span v-if="statusCounts.timeout > 0" class="badge badge-xs badge-error">超时 {{ statusCounts.timeout }}</span>
                                </div>
                    
                                            <div v-if="exploreReports.length > 0">
                                              <template v-for="(item, idx) in exploreReports" :key="`${item.task || idx}-${idx}`">
                                                                                <div v-if="idx > 0" class="divider my-1"></div>
                                                                                <div class="explore-report-card py-3 px-4">                                                  <!-- 标题栏 -->
                                                  <div class="flex items-center justify-between gap-2 mb-2">
                                                    <div class="text-sm font-semibold text-base-content">{{ item.task || `任务 ${idx + 1}` }}</div>
                                                    <div class="flex items-center gap-1.5">
                                                      <span class="badge badge-xs" :class="reportStatusClass(item.status)">{{ reportStatusLabel(item.status) }}</span>
                                                      <span class="text-xs text-base-content/50">{{ Number(item.usedCalls || 0) }}次</span>
                                                    </div>
                                                  </div>
                                
                                                  <!-- 内容区 -->
                                                  <div class="space-y-2">
                                                    <div class="text-sm text-base-content/90 whitespace-pre-wrap leading-relaxed">{{ item.answer || item.summary || '无结论' }}</div>
                                
                                                    <!-- 见解 -->
                                                    <div v-if="item.insights && item.insights.length > 0">
                                                      <div class="text-xs font-medium text-base-content/60 mb-1">见解</div>
                                                      <div v-for="(insight, i2) in item.insights" :key="`insight-${idx}-${i2}`" class="text-xs text-base-content/80 pl-2 border-l-2 border-base-300">
                                                        {{ i2 + 1 }}. {{ insight }}
                                                      </div>
                                                    </div>
                                
                                                    <!-- 引用 -->
                                                    <div v-if="item.references && item.references.length > 0">
                                                      <div class="text-xs font-medium text-base-content/60 mb-1.5">相关文件</div>
                                                      <div class="flex flex-wrap gap-1.5">
                                                        <template v-for="(refText, r2) in item.references" :key="`ref-${idx}-${r2}`">
                                                          <button
                                                            v-if="buildRawLinkFromReference(refText)"
                                                            class="text-xs font-mono text-base-content px-2 py-0.5 border-l-2 border-primary bg-base-200/50 hover:bg-base-200 transition-colors internal-doc-link"
                                                            :data-raw-link="buildRawLinkFromReference(refText)"
                                                            :data-snippet="item.answer || item.summary || ''"
                                                            @click="handleLinkClick"
                                                          >
                                                            {{ refText }}
                                                          </button>
                                                          <span v-else class="text-xs font-mono text-base-content/60 px-2 py-0.5 border-l-2 border-base-300 bg-base-200/50">{{ refText }}</span>
                                                        </template>
                                                      </div>
                                                    </div>
                                
                                                    <!-- 错误 -->
                                                    <div v-if="item.error" class="text-xs text-error">{{ item.error }}</div>
                                                  </div>
                                                </div>
                                              </template>
                                            </div>                              </div>
          <!-- Search 结果 -->
          <div v-else-if="parsedResults.length > 0" class="pt-2 px-1">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-base-content/50">
                找到 {{ isGrouped ? totalFiles : parsedResults.length }} 个结果
              </span>
            </div>
            <div>
              <template v-if="isGrouped">
                <template v-for="(group, index) in parsedResults" :key="index">
                  <div v-if="index > 0" class="divider my-1"></div>
                  <div class="py-2 px-3">
                    <!-- 文件标题 -->
                    <button
                      class="search-result-item internal-doc-link w-full text-left group"
                      :data-path="group.path || ''"
                      :data-raw-link="`[[${group.title || extractFileName(group.path || '')}|path:${group.path || ''}]]`"
                      @click="handleLinkClick"
                    >
                      <div class="flex items-center justify-between gap-3">
                        <span class="text-sm font-semibold text-base-content group-hover:text-primary transition-colors truncate">
                          {{ group.title || extractFileName(group.path || '') }}
                        </span>
                        <span class="text-xs text-base-content/50 shrink-0">
                          {{ (isGroupedResult(group) ? group.hitCount : 0) }} 处
                        </span>
                      </div>
                      <div class="text-[10px] text-base-content/40 truncate font-mono mt-0.5">
                        {{ group.path }}
                      </div>
                    </button>

                    <!-- 命中位置 -->
                    <div v-if="isGroupedResult(group) && group.hits && group.hits.length > 0" class="mt-2 space-y-1">
                      <div
                        v-for="(hit, hitIndex) in group.hits"
                        :key="hitIndex"
                        class="search-result-item internal-doc-link relative pl-2 group cursor-pointer"
                        :data-path="group.path || ''"
                        :data-raw-link="`[[${group.title || extractFileName(group.path || '')}|path:${group.path || ''}:${hit.line}]]`"
                        :data-snippet="hit.snippet.replace(/^>\s*/, '').replace(/\.\.\.$/, '')"
                        @click="handleLinkClick"
                      >
                        <div class="absolute left-0 top-0.5 bottom-0.5 w-0.5 bg-primary/50 rounded-full"></div>
                        <div class="flex items-start gap-2">
                          <span class="text-[10px] text-base-content/50 font-mono shrink-0 pt-0.5">L{{ hit.line }}</span>
                          <span class="text-xs text-base-content/80 font-mono leading-relaxed">
                            {{ hit.snippet }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </template>

              <template v-else>
                <template v-for="(item, index) in parsedResults" :key="index">
                  <div v-if="index > 0" class="divider my-1"></div>
                  <button
                    class="search-result-item internal-doc-link w-full text-left group py-2 px-3"
                    :data-path="item.path || ''"
                    :data-raw-link="`[[${item.title || extractFileName(item.path || '')}|path:${item.path || ''}${(item as SearchResult).line ? ':' + (item as SearchResult).line : ''}]]`"
                    @click="handleLinkClick"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <span class="text-sm font-semibold text-base-content group-hover:text-primary transition-colors truncate">
                        {{ item.title || extractFileName(item.path || '') }}
                      </span>
                      <span v-if="(item as SearchResult).line" class="text-[10px] text-base-content/50 font-mono shrink-0">
                        L{{ (item as SearchResult).line }}
                      </span>
                    </div>
                    <div v-if="(item as SearchResult).snippet" class="relative pl-2 mt-1">
                      <div class="absolute left-0 top-0.5 bottom-0.5 w-0.5 bg-primary/50 rounded-full"></div>
                      <span class="text-xs text-base-content/70 font-mono leading-relaxed">
                        {{ (item as SearchResult).snippet }}
                      </span>
                    </div>
                    <div class="text-[10px] text-base-content/40 truncate font-mono mt-0.5">
                      {{ item.path }}
                    </div>
                  </button>
                </template>
              </template>
            </div>
          </div>

          <!-- 原始内容 fallback -->
          <div v-else class="pt-2">
            <div class="text-xs font-bold text-base-content/50 uppercase tracking-wider mb-2">原始响应内容</div>
            <pre class="whitespace-pre-wrap break-all font-mono text-xs bg-base-100 border border-base-200 p-3 rounded-xl text-base-content/80">{{ formattedContent }}</pre>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { Compass, FileText, List, Search, Wrench } from 'lucide-vue-next';
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
  hits?: Array<{ line: number; snippet: string; }>;
  hitCount?: number;
}

interface ExploreReport {
  task?: string;
  status?: 'success' | 'partial' | 'failed' | 'timeout';
  answer?: string;
  insights?: string[];
  references?: string[];
  summary?: string;
  usedCalls?: number;
  maxToolCalls?: number;
  error?: string;
}

interface ParsedData {
  tool: string;
  query: string;
  results: Array<SearchResult | GroupedSearchResult>;
  grouped: boolean;
  message: string;
  reports: ExploreReport[];
}

interface Props {
  content?: string;
  toolName?: string;
  toolInput?: Record<string, unknown>;
  status?: string;
  isPending?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  content: '',
  toolName: '',
  toolInput: () => ({}),
  status: 'done',
  isPending: false,
});

const toolResultCard = ref<HTMLElement | null>(null);
const resultExpanded = ref<boolean>(false);

watch(() => props.isPending, (pending) => {
  if (pending) resultExpanded.value = false;
}, { immediate: true });

const handleLinkClick = async (event: Event) => {
  const target = (event.target as HTMLElement).closest('.internal-doc-link') as HTMLElement | null;
  if (!target || !target.dataset.rawLink) return;
  event.preventDefault();
  event.stopPropagation();

  const rawLink = target.dataset.rawLink;
  let snippet = target.dataset.snippet;
  if (snippet) snippet = snippet.replace(/^>\s*/, '').replace(/\.\.\.$/, '');

  try {
    const result: LinkResolutionResult = await linkProcessorService.resolveLink(rawLink);
    if (result.isValid && result.resolvedPath) {
      const docViewerStore = useDocumentViewerStore();
      docViewerStore.open(result.resolvedPath, undefined, snippet ? [snippet] : undefined);
      return;
    }
    alert(`链接指向的路径 "${result.originalPath}" 无法被解析或找到。`);
  } catch (error) {
    console.error('处理链接点击时出错:', error);
    alert(`链接处理失败: ${error}`);
  }
};

const isGroupedResult = (item: unknown): item is GroupedSearchResult => {
  return Boolean(item && typeof item === 'object' && 'hits' in (item as Record<string, unknown>) && Array.isArray((item as GroupedSearchResult).hits));
};

onMounted(() => {
  if (toolResultCard.value) {
    toolResultCard.value.addEventListener('click', handleLinkClick);
  }
});

onUnmounted(() => {
  if (toolResultCard.value) {
    toolResultCard.value.removeEventListener('click', handleLinkClick);
  }
});

function parseJsonContent(content: string): unknown {
  const text = String(content || '').trim();
  if (!text) return null;
  try { return JSON.parse(text); } catch { /* ignore */ }
  const firstBrace = text.indexOf('{');
  const lastBrace = text.lastIndexOf('}');
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    try { return JSON.parse(text.slice(firstBrace, lastBrace + 1)); } catch { /* ignore */ }
  }
  return null;
}

const parsedData = computed<ParsedData>(() => {
  const parsed = parseJsonContent(props.content);
  if (!parsed || typeof parsed !== 'object') {
    return { tool: '', query: '', results: [], grouped: false, message: '', reports: [] };
  }
  const data = parsed as Record<string, unknown>;

  if (data.tool === 'explore') {
    return {
      tool: 'explore',
      query: '',
      results: [],
      grouped: false,
      message: String(data.message || ''),
      reports: Array.isArray(data.reports) ? (data.reports as ExploreReport[]) : [],
    };
  }

  if (data.tool === 'search_docs') {
    return {
      tool: 'search_docs',
      query: String(data.query || ''),
      results: Array.isArray(data.results) ? (data.results as Array<SearchResult | GroupedSearchResult>) : [],
      grouped: data.grouped === true,
      message: String(data.message || ''),
      reports: [],
    };
  }

  if (typeof data.query === 'string' && Array.isArray(data.results)) {
    return {
      tool: typeof data.tool === 'string' ? data.tool : '',
      query: data.query,
      results: data.results as Array<SearchResult | GroupedSearchResult>,
      grouped: data.grouped === true,
      message: String(data.message || ''),
      reports: [],
    };
  }

  if (Array.isArray(data.docs)) {
    return {
      tool: typeof data.tool === 'string' ? data.tool : '',
      query: '',
      results: data.docs as Array<SearchResult | GroupedSearchResult>,
      grouped: false,
      message: '',
      reports: [],
    };
  }

  return { tool: '', query: '', results: [], grouped: false, message: '', reports: [] };
});

const toolInputRecord = computed(() => {
  if (!props.toolInput || typeof props.toolInput !== 'object') return {} as Record<string, unknown>;
  return props.toolInput;
});

const resolvedToolName = computed(() => {
  return String(props.toolName || parsedData.value.tool || 'unknown_tool');
});

const toolDisplayNameMap: Record<string, string> = {
  search_docs: '检索',
  read_doc: '阅读',
  explore: '探索',
  ask_choice: '询问',
};

const toolDisplayName = computed(() => {
  return toolDisplayNameMap[resolvedToolName.value] || resolvedToolName.value;
});

const toolIcon = computed(() => {
  switch (resolvedToolName.value) {
    case 'search_docs': return Search;
    case 'read_doc': return FileText;
    case 'explore': return Compass;
    case 'ask_choice': return List;
    default: return Wrench;
  }
});

const isPending = computed(() => Boolean(props.isPending));
const pendingText = computed(() => String(props.content || '').trim() || '执行中...');

const isErrorResult = computed(() => {
  if (isPending.value) return false;
  const text = String(props.content || '').trim();
  return text.startsWith('错误(') || text.startsWith('错误:') || text.startsWith('ERROR(');
});

const iconBgClass = computed(() => {
  if (isPending.value) return 'bg-info/30';
  if (isErrorResult.value) return 'bg-error/20';
  return 'bg-success/20';
});

const statusIcon = computed(() => {
  if (isPending.value) return '';
  if (isErrorResult.value) return '✗';
  return '✓';
});

const statusIconClass = computed(() => {
  if (isPending.value) return 'opacity-50';
  if (isErrorResult.value) return 'text-error';
  return 'text-success';
});

const exploreReports = computed(() => parsedData.value.reports || []);
const isExploreResult = computed(() => resolvedToolName.value === 'explore' || parsedData.value.tool === 'explore');
const parsedResults = computed(() => parsedData.value.results as Array<SearchResult | GroupedSearchResult>);
const isGrouped = computed(() => parsedData.value.grouped);
const totalFiles = computed(() => parsedResults.value.length);

const requestedTasks = computed(() => {
  const raw = (toolInputRecord.value as Record<string, unknown>).tasks;
  if (Array.isArray(raw)) return raw.map(item => String(item || '').trim()).filter(Boolean);
  if (typeof raw === 'string') {
    const text = raw.trim();
    if (!text) return [];
    if (text.startsWith('[')) {
      try {
        const parsed = JSON.parse(text);
        if (Array.isArray(parsed)) return parsed.map(item => String(item || '').trim()).filter(Boolean);
      } catch { /* ignore */ }
    }
    return [text];
  }
  return [];
});

const expectedTaskCount = computed<number | null>(() => {
  if (requestedTasks.value.length > 0) return requestedTasks.value.length;
  if (exploreReports.value.length > 0) return exploreReports.value.length;
  return null;
});

const completedTaskCount = computed(() => exploreReports.value.length);
const totalUsedCalls = computed(() => exploreReports.value.reduce((sum, item) => sum + Number(item.usedCalls || 0), 0));

const statusCounts = computed(() => {
  return exploreReports.value.reduce((acc, item) => {
    const key = String(item.status || '');
    if (key === 'success') acc.success += 1;
    if (key === 'partial') acc.partial += 1;
    if (key === 'failed') acc.failed += 1;
    if (key === 'timeout') acc.timeout += 1;
    return acc;
  }, { success: 0, partial: 0, failed: 0, timeout: 0 });
});

// 极简摘要 - 单行显示
const compactSummary = computed(() => {
  const tool = resolvedToolName.value;
  const input = toolInputRecord.value as Record<string, unknown>;

  if (tool === 'explore') {
    const count = expectedTaskCount.value !== null ? `${expectedTaskCount.value}任务` : '探索';
    return `${count} · ${totalUsedCalls.value}次调用`;
  }

  if (tool === 'search_docs') {
    const query = String(input.query || '').trim();
    return query.length > 20 ? query.slice(0, 20) + '...' : query || '(空)';
  }

  if (tool === 'read_doc') {
    const path = String(input.path || '').trim();
    return extractFileName(path) || '(未指定)';
  }

  if (tool === 'ask_choice') {
    const q = String(input.question || '').trim();
    return q.length > 20 ? q.slice(0, 20) + '...' : q || '等待选择';
  }

  return '已执行';
});

// 结果计数文本
const resultCountText = computed(() => {
  if (isExploreResult.value) {
    return `${completedTaskCount.value}个结果`;
  }
  if (isGrouped.value) {
    return `${parsedResults.value.length}个文件`;
  }
  return `${parsedResults.value.length}条结果`;
});

const formattedContent = computed(() => {
  const parsed = parseJsonContent(props.content);
  if (parsed && typeof parsed === 'object') {
    return JSON.stringify(parsed, null, 2);
  }
  return props.content;
});

function reportStatusLabel(status?: string): string {
  if (status === 'success') return '成功';
  if (status === 'partial') return '部分成功';
  if (status === 'timeout') return '超时';
  if (status === 'failed') return '失败';
  return '未知';
}

function reportStatusClass(status?: string): string {
  if (status === 'success') return 'badge-success';
  if (status === 'partial') return 'badge-warning';
  if (status === 'timeout' || status === 'failed') return 'badge-error';
  return 'badge-ghost';
}

function reportBorderClass(status?: string): string {
  if (status === 'success') return 'border-t-success';
  if (status === 'partial') return 'border-t-warning';
  if (status === 'timeout' || status === 'failed') return 'border-t-error';
  return 'border-t-base-300';
}

function buildRawLinkFromReference(reference: string): string {
  const text = String(reference || '').trim();
  if (!text) return '';
  const match = text.match(/^(.+?):(\d+(?:-\d+)?)$/);
  if (!match) return '';
  const filePath = match[1];
  const lineToken = match[2];
  const firstLine = lineToken.split('-')[0];
  return `[[${extractFileName(filePath)}|path:${filePath}:${firstLine}]]`;
}
</script>

<style scoped>
.collapse-title {
  padding-right: 2rem; /* 给箭头留空间 */
}

/* 修复折叠状态下 collapse-content 占用空间 */
.collapse:not(:has(input:checked)) .collapse-content {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}
</style>