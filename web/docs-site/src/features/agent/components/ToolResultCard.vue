<template>
  <div class="card card-compact bg-base-100 border border-base-300 shadow-xs rounded-2xl" ref="toolResultCard">
    <div class="card-body p-0">
      <div class="px-3 py-3 border-b border-base-200">
        <div class="flex items-start gap-3">
          <div class="flex h-8 w-8 items-center justify-center rounded-full shrink-0" :class="iconBgClass">
            <component :is="toolIcon" class="h-4 w-4 text-base-content" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <div class="text-sm font-medium text-base-content">{{ cardTitle }}</div>
              <span class="badge badge-xs" :class="statusBadgeClass">{{ statusLabel }}</span>
            </div>
            <div class="text-xs opacity-70 mt-0.5 break-words">{{ callSummary }}</div>
          </div>
        </div>
      </div>

      <div class="collapse collapse-arrow rounded-b-2xl">
        <input type="checkbox" v-model="resultExpanded" />
        <div class="collapse-title py-2 px-3 min-h-0">
          <div class="flex items-center justify-between gap-2">
            <span class="text-xs font-semibold uppercase tracking-wider text-base-content/60">执行结果</span>
            <span v-if="isExploreResult && !isPending && expectedTaskCount !== null" class="text-[11px] text-base-content/60">
              任务 {{ completedTaskCount }}/{{ expectedTaskCount }} · 子调用 {{ totalUsedCalls }} 次
            </span>
          </div>
        </div>

        <div class="collapse-content pt-0 px-3 pb-3">
          <div v-if="isPending" class="flex items-center gap-2 text-xs opacity-80">
            <span class="loading loading-spinner loading-xs"></span>
            <span>{{ pendingText }}</span>
          </div>

          <template v-else>
            <div v-if="isExploreResult" class="space-y-2">
              <div class="flex flex-wrap gap-2">
                <span v-if="expectedTaskCount !== null" class="badge badge-sm badge-ghost">计划任务 {{ expectedTaskCount }}</span>
                <span class="badge badge-sm badge-ghost">返回任务 {{ completedTaskCount }}</span>
                <span class="badge badge-sm badge-primary">子调用 {{ totalUsedCalls }} 次</span>
                <span v-if="configuredMaxToolCalls > 0" class="badge badge-sm badge-ghost">单任务上限 {{ configuredMaxToolCalls }}</span>
                <span v-if="statusCounts.success > 0" class="badge badge-sm badge-success">成功 {{ statusCounts.success }}</span>
                <span v-if="statusCounts.partial > 0" class="badge badge-sm badge-warning">部分 {{ statusCounts.partial }}</span>
                <span v-if="statusCounts.failed > 0" class="badge badge-sm badge-error">失败 {{ statusCounts.failed }}</span>
                <span v-if="statusCounts.timeout > 0" class="badge badge-sm badge-error">超时 {{ statusCounts.timeout }}</span>
              </div>

              <div v-if="exploreReports.length > 0" class="space-y-2">
                <div
                  v-for="(item, idx) in exploreReports"
                  :key="`${item.task || idx}-${idx}`"
                  class="rounded-xl border border-base-200 bg-base-100 p-3"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="text-sm font-medium">{{ item.task || `任务 ${idx + 1}` }}</div>
                    <div class="flex items-center gap-1">
                      <span class="badge badge-xs" :class="reportStatusClass(item.status)">{{ reportStatusLabel(item.status) }}</span>
                      <span class="badge badge-xs badge-ghost">{{ Number(item.usedCalls || 0) }}/{{ Number(item.maxToolCalls || configuredMaxToolCalls || 0) }}</span>
                    </div>
                  </div>

                  <div class="mt-2 text-xs opacity-85 whitespace-pre-wrap">{{ item.answer || item.summary || '无结论' }}</div>

                  <div v-if="item.insights && item.insights.length > 0" class="mt-2 text-xs">
                    <div class="font-semibold opacity-80">见解</div>
                    <div v-for="(insight, i2) in item.insights" :key="`insight-${idx}-${i2}`" class="opacity-70">
                      {{ i2 + 1 }}. {{ insight }}
                    </div>
                  </div>

                  <div v-if="item.references && item.references.length > 0" class="mt-2 text-xs">
                    <div class="font-semibold opacity-80">相关文件行号</div>
                    <div class="mt-1 flex flex-wrap gap-1.5">
                      <template v-for="(refText, r2) in item.references" :key="`ref-${idx}-${r2}`">
                        <button
                          v-if="buildRawLinkFromReference(refText)"
                          class="badge badge-sm badge-outline internal-doc-link font-mono"
                          :data-raw-link="buildRawLinkFromReference(refText)"
                          :data-snippet="item.answer || item.summary || ''"
                          @click="handleLinkClick"
                        >
                          {{ refText }}
                        </button>
                        <span v-else class="badge badge-sm badge-outline font-mono">{{ refText }}</span>
                      </template>
                    </div>
                  </div>

                  <div v-if="item.error" class="mt-2 text-[11px] text-error">错误: {{ item.error }}</div>
                </div>
              </div>

              <div v-else class="text-xs opacity-70">暂无可展示的探索结果。</div>
            </div>

            <div v-else-if="parsedResults.length > 0" class="search-results-list">
              <div class="flex items-center justify-between mb-2 px-1">
                <span class="text-xs font-bold text-base-content/50 uppercase tracking-wider">
                  找到 {{ isGrouped ? totalFiles : parsedResults.length }} 个相关结果
                </span>
              </div>
              <div class="space-y-2">
                <template v-if="isGrouped">
                  <div
                    v-for="(group, index) in parsedResults"
                    :key="index"
                    class="search-result-group border border-base-200 rounded-xl bg-base-100"
                  >
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

                <template v-else>
                  <button
                    v-for="(item, index) in parsedResults"
                    :key="index"
                    class="search-result-item internal-doc-link w-full text-left group relative flex flex-col gap-2 p-3 rounded-xl bg-base-300 border border-base-200 hover:border-primary/30 hover:shadow-sm transition-all duration-200"
                    :data-path="item.path || ''"
                    :data-raw-link="`[[${item.title || extractFileName(item.path || '')}|path:${item.path || ''}${(item as SearchResult).line ? ':' + (item as SearchResult).line : ''}]]`"
                    @click="handleLinkClick"
                  >
                    <div class="flex items-start justify-between gap-3 w-full">
                      <div class="flex items-center gap-2 min-w-0">
                        <span class="font-semibold text-sm text-base-content group-hover:text-accent-content transition-colors truncate">
                          {{ item.title || extractFileName(item.path || '') }}
                        </span>
                      </div>
                      <div v-if="(item as SearchResult).line" class="badge badge-sm badge-ghost shrink-0 font-mono text-[10px] opacity-70">
                        Ln {{ (item as SearchResult).line }}
                      </div>
                    </div>

                    <div v-if="(item as SearchResult).snippet" class="relative pl-3 w-full">
                      <div class="absolute left-0 top-1 bottom-1 w-0.5 bg-base-300 group-hover:bg-accent-content transition-colors rounded-full"></div>
                      <div class="text-xs text-base-content/70 line-clamp-2 leading-relaxed font-mono">
                        {{ (item as SearchResult).snippet }}
                      </div>
                    </div>

                    <div class="flex items-center gap-1.5 px-1 mt-0.5 w-full">
                      <span class="text-[10px] text-base-content/40 truncate font-mono">{{ item.path }}</span>
                    </div>
                  </button>
                </template>
              </div>
            </div>

            <div v-else class="mt-1">
              <div class="text-xs font-bold text-base-content/50 uppercase tracking-wider mb-2">原始响应内容</div>
              <pre class="whitespace-pre-wrap break-all font-mono text-xs bg-base-100 border border-base-200 p-3 rounded-xl text-base-content/80">{{ formattedContent }}</pre>
            </div>
          </template>
        </div>
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
  hits?: Array<{
    line: number;
    snippet: string;
  }>;
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

watch(
  () => props.isPending,
  (pending) => {
    if (pending) {
      resultExpanded.value = false;
    }
  },
  { immediate: true }
);

const handleLinkClick = async (event: Event) => {
  const target = (event.target as HTMLElement).closest('.internal-doc-link') as HTMLElement | null;
  if (!target || !target.dataset.rawLink) return;

  event.preventDefault();
  event.stopPropagation();

  const rawLink = target.dataset.rawLink;
  let snippet = target.dataset.snippet;
  if (snippet) {
    snippet = snippet.replace(/^>\s*/, '').replace(/\.\.\.$/, '');
  }

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

  try {
    return JSON.parse(text);
  } catch {
    // ignore
  }

  const firstBrace = text.indexOf('{');
  const lastBrace = text.lastIndexOf('}');
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    try {
      return JSON.parse(text.slice(firstBrace, lastBrace + 1));
    } catch {
      // ignore
    }
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
      query: '展开查看文档',
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
  search_docs: '检索文档',
  read_doc: '阅读文档',
  explore: '探索',
  ask_choice: '询问选择',
};

const toolIcon = computed(() => {
  switch (resolvedToolName.value) {
    case 'search_docs':
      return Search;
    case 'read_doc':
      return FileText;
    case 'explore':
      return Compass;
    case 'ask_choice':
      return List;
    default:
      return Wrench;
  }
});

const isPending = computed(() => Boolean(props.isPending));
const pendingText = computed(() => {
  const text = String(props.content || '').trim();
  return text || '工具正在执行中...';
});

const isErrorResult = computed(() => {
  if (isPending.value) return false;
  const text = String(props.content || '').trim();
  if (!text) return false;
  return text.startsWith('错误(') || text.startsWith('错误:') || text.startsWith('ERROR(');
});

const statusLabel = computed(() => {
  if (isPending.value) return '执行中';
  if (isErrorResult.value) return '失败';
  return '已完成';
});

const statusBadgeClass = computed(() => {
  if (isPending.value) return 'badge-info';
  if (isErrorResult.value) return 'badge-error';
  return 'badge-success';
});

const iconBgClass = computed(() => {
  if (isPending.value) return 'bg-info/30';
  if (isErrorResult.value) return 'bg-error/20';
  return 'bg-success/30';
});

const exploreReports = computed(() => parsedData.value.reports || []);
const isExploreResult = computed(() => resolvedToolName.value === 'explore' || parsedData.value.tool === 'explore');
const parsedResults = computed(() => parsedData.value.results as Array<SearchResult | GroupedSearchResult>);
const isGrouped = computed(() => parsedData.value.grouped);
const totalFiles = computed(() => parsedResults.value.length);

const requestedTasks = computed(() => {
  const raw = (toolInputRecord.value as Record<string, unknown>).tasks;
  if (Array.isArray(raw)) {
    return raw.map(item => String(item || '').trim()).filter(Boolean);
  }
  if (typeof raw === 'string') {
    const text = raw.trim();
    if (!text) return [];
    if (text.startsWith('[')) {
      try {
        const parsed = JSON.parse(text);
        if (Array.isArray(parsed)) {
          return parsed.map(item => String(item || '').trim()).filter(Boolean);
        }
      } catch {
        // ignore
      }
    }
    return [text];
  }
  return [];
});

const taskCountFromContent = computed<number | null>(() => {
  const content = String(props.content || '');
  const match = content.match(/(\d+)\s*个任务/);
  if (!match) return null;
  const count = Number(match[1]);
  return Number.isFinite(count) && count >= 0 ? count : null;
});

const expectedTaskCount = computed<number | null>(() => {
  if (requestedTasks.value.length > 0) return requestedTasks.value.length;
  if (taskCountFromContent.value !== null) return taskCountFromContent.value;
  if (exploreReports.value.length > 0) return exploreReports.value.length;
  return null;
});

const completedTaskCount = computed(() => exploreReports.value.length);
const totalUsedCalls = computed(() => {
  return exploreReports.value.reduce((sum, item) => sum + Number(item.usedCalls || 0), 0);
});

const configuredMaxToolCalls = computed(() => {
  const fromInput = Number((toolInputRecord.value as Record<string, unknown>).maxToolCalls || 0);
  if (Number.isFinite(fromInput) && fromInput > 0) {
    return Math.floor(fromInput);
  }
  const fromReport = Number(exploreReports.value[0]?.maxToolCalls || 0);
  if (Number.isFinite(fromReport) && fromReport > 0) {
    return Math.floor(fromReport);
  }
  return 0;
});

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

function timeoutLabelFromInput(): string {
  const timeoutMs = Number((toolInputRecord.value as Record<string, unknown>).timeoutMs || 0);
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) return '';
  const minutes = Math.round((timeoutMs / 60000) * 10) / 10;
  return `${minutes} 分钟`;
}

const callSummary = computed(() => {
  const tool = resolvedToolName.value;
  const input = toolInputRecord.value as Record<string, unknown>;

  if (tool === 'explore') {
    const taskText = expectedTaskCount.value !== null
      ? `${expectedTaskCount.value} 个`
      : '若干';
    const maxCalls = configuredMaxToolCalls.value > 0 ? `，单任务上限 ${configuredMaxToolCalls.value} 次` : '';
    const timeout = timeoutLabelFromInput();
    const timeoutText = timeout ? `，超时 ${timeout}` : '';
    return `发起 ${taskText}探索子任务${maxCalls}${timeoutText}。`;
  }

  if (tool === 'search_docs') {
    const query = String(input.query || '').trim();
    const path = String(input.path || '').trim();
    const maxResults = Number(input.maxResults || 0);
    const resultLimit = Number.isFinite(maxResults) && maxResults > 0 ? `，最多 ${Math.floor(maxResults)} 条` : '';
    return `query: ${query || '(空)'}${path ? `，path: ${path}` : ''}${resultLimit}`;
  }

  if (tool === 'read_doc') {
    const path = String(input.path || '').trim();
    const range = String(input.line_range || '').trim();
    return `${path || '(未指定路径)'}${range ? `，行 ${range}` : ''}`;
  }

  if (tool === 'ask_choice') {
    return String(input.question || '等待用户选择').trim();
  }

  return '已调用工具。';
});

const cardTitle = computed(() => {
  const display = toolDisplayNameMap[resolvedToolName.value] || resolvedToolName.value;
  return `工具执行 · ${display}`;
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
