<template>
  <div class="card card-border bg-base-100 shadow-md mb-6">
    <div class="card-body">
      <h2 class="card-title mb-3">数据迁移</h2>
      <p class="text-sm text-base-content/70 mb-4">
        支持导出/导入全部用户数据，并可单独导出/导入记忆库。
      </p>

      <div class="alert alert-warning mb-4">
        <span class="text-sm">
          文件包含敏感信息（如 API Key 与聊天内容），请仅在可信设备保存和导入。
        </span>
      </div>

      <div class="space-y-3">
        <div class="font-medium">导出</div>
        <div class="flex items-center gap-3 flex-wrap">
          <button
            class="btn btn-primary"
            :disabled="isExporting"
            @click="handleExport"
          >
            <span
              v-if="isExporting"
              class="loading loading-spinner loading-sm"
              aria-hidden="true"
            ></span>
            导出全部用户数据（含记忆库）
          </button>
          <span v-if="exportMessage" class="text-xs text-base-content/70">
            {{ exportMessage }}
          </span>
        </div>
      </div>

      <div class="divider my-4"></div>

      <div class="space-y-3">
        <div class="font-medium">导入</div>
        <div class="flex items-center gap-3 flex-wrap">
          <input
            ref="fileInputRef"
            type="file"
            accept=".json,application/json"
            class="hidden"
            @change="handleFileSelected"
          />
          <button class="btn btn-outline btn-sm" @click="triggerFilePicker">
            选择导入文件
          </button>
          <span class="text-xs text-base-content/70">
            {{ selectedFileName || '未选择文件' }}
          </span>
        </div>

        <div class="form-control w-full max-w-xs">
          <label class="label">
            <span class="label-text text-sm">冲突处理策略</span>
          </label>
          <select v-model="importStrategy" class="select select-bordered select-sm">
            <option value="preview">仅预览（不写入）</option>
            <option value="merge">合并导入（保留本地并叠加）</option>
            <option value="overwrite">覆盖导入（用文件替换）</option>
          </select>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <button
            class="btn btn-secondary btn-sm"
            :disabled="!importPayload || isImporting"
            @click="handleImport"
          >
            <span
              v-if="isImporting"
              class="loading loading-spinner loading-sm"
              aria-hidden="true"
            ></span>
            执行导入
          </button>
          <span v-if="importMessage" class="text-xs text-base-content/70">
            {{ importMessage }}
          </span>
        </div>

        <div v-if="importSummary" class="text-xs bg-base-200/60 rounded-lg p-3 space-y-1">
          <div>Schema: {{ importSummary.schemaVersion }}</div>
          <div>导出时间: {{ importSummary.exportedAt || '未知' }}</div>
          <div>AI 配置: {{ importSummary.configs }}</div>
          <div>自定义指令: {{ importSummary.customInstructions }}</div>
          <div>自定义角色: {{ importSummary.customPersonas }}</div>
          <div>会话数量: {{ importSummary.sessionCount }}</div>
          <div>会话存储键: {{ importSummary.persistedSessionKeys }}</div>
          <div>最近角色记录: {{ importSummary.lastUsedRoles }}</div>
          <div>记忆库记录: {{ importSummary.memoryRecords }}</div>
        </div>
      </div>

      <div class="divider my-4"></div>

      <div class="space-y-3">
        <div class="font-medium">记忆库（单独）</div>

        <div class="flex items-center gap-3 flex-wrap">
          <button
            class="btn btn-primary btn-sm"
            :disabled="isMemoryExporting"
            @click="handleMemoryExport"
          >
            <span
              v-if="isMemoryExporting"
              class="loading loading-spinner loading-sm"
              aria-hidden="true"
            ></span>
            导出记忆 JSON
          </button>
          <button
            class="btn btn-outline btn-sm"
            :disabled="isMemoryListLoading"
            @click="openMemoryBrowser"
          >
            浏览记忆库
          </button>
          <span v-if="memoryExportMessage" class="text-xs text-base-content/70">
            {{ memoryExportMessage }}
          </span>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <input
            ref="memoryFileInputRef"
            type="file"
            accept=".json,application/json"
            class="hidden"
            @change="handleMemoryFileSelected"
          />
          <button class="btn btn-outline btn-sm" @click="triggerMemoryFilePicker">
            选择记忆 JSON 文件
          </button>
          <span class="text-xs text-base-content/70">
            {{ selectedMemoryFileName || '未选择文件' }}
          </span>
        </div>

        <div class="form-control w-full max-w-xs">
          <label class="label">
            <span class="label-text text-sm">记忆导入策略</span>
          </label>
          <select v-model="memoryImportStrategy" class="select select-bordered select-sm">
            <option value="preview">仅预览（不写入）</option>
            <option value="merge">合并导入（保留本地并叠加）</option>
            <option value="overwrite">覆盖导入（仅保留文件记忆）</option>
          </select>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <button
            class="btn btn-secondary btn-sm"
            :disabled="!memoryImportPayload || isMemoryImporting"
            @click="handleMemoryImport"
          >
            <span
              v-if="isMemoryImporting"
              class="loading loading-spinner loading-sm"
              aria-hidden="true"
            ></span>
            执行记忆导入
          </button>
          <span v-if="memoryImportMessage" class="text-xs text-base-content/70">
            {{ memoryImportMessage }}
          </span>
        </div>

        <div v-if="memoryImportSummary" class="text-xs bg-base-200/60 rounded-lg p-3 space-y-1">
          <div>Schema: {{ memoryImportSummary.schemaVersion }}</div>
          <div>导出时间: {{ memoryImportSummary.exportedAt || '未知' }}</div>
          <div>记忆库记录: {{ memoryImportSummary.memoryRecords }}</div>
        </div>
      </div>
    </div>
  </div>

  <div v-if="isMemoryBrowserOpen" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" @click.self="closeMemoryBrowser">
    <div class="card bg-base-100 shadow-xl w-full max-w-2xl max-h-[85vh]">
      <div class="card-body p-4 h-full overflow-hidden">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-base">记忆库</h3>
          <div class="flex items-center gap-2">
            <span class="text-xs text-base-content/50">{{ memoryRecords.length }} 条</span>
            <button class="btn btn-ghost btn-sm btn-circle" @click="closeMemoryBrowser">✕</button>
          </div>
        </div>

        <div v-if="isMemoryListLoading" class="flex items-center gap-2 text-sm text-base-content/70 py-6 justify-center">
          <span class="loading loading-spinner loading-sm" aria-hidden="true"></span>
        </div>

        <div v-else-if="pagedMemoryRecords.length === 0" class="text-sm text-base-content/50 py-12 text-center">
          暂无记忆
        </div>

        <div v-else class="space-y-2 overflow-y-auto pr-1" style="max-height: calc(85vh - 140px);">
          <div 
            v-for="record in pagedMemoryRecords" 
            :key="record.id" 
            class="group relative card bg-base-200 p-3"
          >
            <div class="text-sm text-base-content/90 whitespace-pre-wrap pr-8">{{ record.content }}</div>
            <div class="flex items-center gap-2 mt-2">
              <div class="flex flex-wrap gap-1 flex-1">
                <span 
                  v-for="(kw, i) in record.keywords" 
                  :key="i" 
                  class="badge badge-xs badge-primary"
                >
                  {{ kw }}
                </span>
              </div>
              <span class="text-[10px] text-base-content/40 shrink-0">{{ formatMemoryTime(record.updatedAt) }}</span>
            </div>
            <button 
              class="absolute right-2 top-2 opacity-30 group-hover:opacity-100 p-1.5 rounded-md bg-base-300/50 hover:bg-error/20 transition-all"
              @click="handleDeleteMemory(record.id)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-base-content/60 hover:text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div v-if="memoryTotalPages > 1" class="flex items-center justify-center gap-2 mt-3 pt-2 border-t border-base-200">
          <button class="btn btn-ghost btn-xs" :disabled="memoryPage <= 1" @click="goPrevMemoryPage">
            ‹
          </button>
          <span class="text-xs text-base-content/50">{{ memoryPage }} / {{ memoryTotalPages }}</span>
          <button class="btn btn-ghost btn-xs" :disabled="memoryPage >= memoryTotalPages" @click="goNextMemoryPage">
            ›
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import logger from '@/features/app/services/loggerService';
import { useAppStore } from '@/features/app/stores/app';
import { useConfigStore } from '@/features/app/stores/config';
import { useThemeStore } from '@/features/app/stores/themeStore';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import memoryStoreService, { type MemoryRecord } from '@/features/memory/services/memoryStoreService';
import {
  exportUserData,
  importUserData,
  previewUserDataImport,
  readUserDataImportFile,
  exportMemoryLibrary,
  importMemoryLibrary,
  previewMemoryLibraryImport,
  readMemoryLibraryImportFile,
  type MemoryLibraryImportPayload,
  type MemoryLibraryImportSummary,
  type UserDataImportPayload,
  type UserDataImportSummary,
  type UserDataImportStrategy,
} from '../services/userDataExportService';

const appStore = useAppStore();
const configStore = useConfigStore();
const themeStore = useThemeStore();
const agentStore = useAgentStore();

const fileInputRef = ref<HTMLInputElement | null>(null);
const isExporting = ref(false);
const isImporting = ref(false);
const exportMessage = ref('');
const importMessage = ref('');
const selectedFileName = ref('');
const importStrategy = ref<UserDataImportStrategy>('preview');
const importPayload = ref<UserDataImportPayload | null>(null);
const importSummary = ref<UserDataImportSummary | null>(null);

const memoryFileInputRef = ref<HTMLInputElement | null>(null);
const isMemoryExporting = ref(false);
const isMemoryImporting = ref(false);
const memoryExportMessage = ref('');
const memoryImportMessage = ref('');
const selectedMemoryFileName = ref('');
const memoryImportStrategy = ref<UserDataImportStrategy>('preview');
const memoryImportPayload = ref<MemoryLibraryImportPayload | null>(null);
const memoryImportSummary = ref<MemoryLibraryImportSummary | null>(null);
const isMemoryBrowserOpen = ref(false);
const isMemoryListLoading = ref(false);
const memoryBrowserMessage = ref('');
const memoryRecords = ref<MemoryRecord[]>([]);
const memoryPage = ref(1);
const MEMORY_PAGE_SIZE = 10;

const memoryTotalPages = computed(() => {
  const total = Math.ceil(memoryRecords.value.length / MEMORY_PAGE_SIZE);
  return Math.max(1, total);
});

const pagedMemoryRecords = computed(() => {
  const start = (memoryPage.value - 1) * MEMORY_PAGE_SIZE;
  return memoryRecords.value.slice(start, start + MEMORY_PAGE_SIZE);
});

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function triggerFilePicker(): void {
  fileInputRef.value?.click();
}

function triggerMemoryFilePicker(): void {
  memoryFileInputRef.value?.click();
}

async function handleFileSelected(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  try {
    selectedFileName.value = file.name;
    const payload = await readUserDataImportFile(file);
    importPayload.value = payload;

    const preview = previewUserDataImport(payload);
    importSummary.value = preview.summary;
    importMessage.value = '文件解析成功，可预览或导入。';
  } catch (error) {
    logger.error('[DataExportSection] 读取导入文件失败:', error);
    importPayload.value = null;
    importSummary.value = null;
    importMessage.value = '文件解析失败，请确认 JSON 格式正确。';
  } finally {
    input.value = '';
  }
}

async function handleExport(): Promise<void> {
  if (isExporting.value) return;

  const confirmed = window.confirm(
    '导出文件会包含 API Key 和聊天记录等敏感信息，确认继续导出吗？'
  );
  if (!confirmed) return;

  isExporting.value = true;
  exportMessage.value = '';

  try {
    const result = await exportUserData({
      settings: {
        currentDomain: appStore.currentDomain,
        currentTheme: themeStore.currentTheme,
        configs: configStore.configs,
        activeConfigId: configStore.activeConfigId,
      },
      chat: {
        sessions: agentStore.sessions,
        activeSessionIds: agentStore.activeSessionIds,
        activeInstructionId: agentStore.currentInstructionId,
      },
    });

    exportMessage.value = `导出成功: ${result.fileName} (${formatBytes(result.sizeBytes)})`;
  } catch (error) {
    logger.error('[DataExportSection] 导出失败:', error);
    alert('导出失败，请稍后重试或查看控制台日志。');
  } finally {
    isExporting.value = false;
  }
}

async function handleImport(): Promise<void> {
  if (!importPayload.value || isImporting.value) return;

  isImporting.value = true;
  importMessage.value = '';

  try {
    if (importStrategy.value === 'preview') {
      const preview = previewUserDataImport(importPayload.value);
      importSummary.value = preview.summary;
      importMessage.value = '预览完成（未写入任何数据）。';
      return;
    }

    const isOverwrite = importStrategy.value === 'overwrite';
    const confirmed = window.confirm(
      isOverwrite
        ? '将覆盖本地用户数据，确认继续吗？'
        : '将合并导入到本地数据，确认继续吗？'
    );
    if (!confirmed) return;

    const result = await importUserData(
      importPayload.value,
      importStrategy.value as 'merge' | 'overwrite'
    );
    importSummary.value = result.summary;
    importMessage.value = result.applied
      ? `导入完成（策略: ${result.strategy}）。建议刷新页面加载新状态。`
      : '导入未执行。';

    const shouldReload = window.confirm('导入已完成，是否立即刷新页面应用新数据？');
    if (shouldReload) {
      window.location.reload();
    }
  } catch (error) {
    logger.error('[DataExportSection] 导入失败:', error);
    alert('导入失败，请检查文件内容或稍后重试。');
  } finally {
    isImporting.value = false;
  }
}

async function handleMemoryFileSelected(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  try {
    selectedMemoryFileName.value = file.name;
    const payload = await readMemoryLibraryImportFile(file);
    memoryImportPayload.value = payload;

    const preview = previewMemoryLibraryImport(payload);
    memoryImportSummary.value = preview.summary;
    memoryImportMessage.value = '记忆文件解析成功，可预览或导入。';
  } catch (error) {
    logger.error('[DataExportSection] 读取记忆导入文件失败:', error);
    memoryImportPayload.value = null;
    memoryImportSummary.value = null;
    memoryImportMessage.value = '记忆文件解析失败：必须为 JSON 数组格式。';
  } finally {
    input.value = '';
  }
}

async function handleMemoryExport(): Promise<void> {
  if (isMemoryExporting.value) return;

  const confirmed = window.confirm('将仅导出记忆库 JSON，确认继续吗？');
  if (!confirmed) return;

  isMemoryExporting.value = true;
  memoryExportMessage.value = '';

  try {
    const result = await exportMemoryLibrary();
    memoryExportMessage.value = `记忆导出成功: ${result.fileName} (${formatBytes(result.sizeBytes)})`;
  } catch (error) {
    logger.error('[DataExportSection] 记忆导出失败:', error);
    alert('记忆导出失败，请稍后重试或查看控制台日志。');
  } finally {
    isMemoryExporting.value = false;
  }
}

async function refreshMemoryRecords(preservePage = false): Promise<void> {
  isMemoryListLoading.value = true;
  memoryBrowserMessage.value = '';
  try {
    const list = await memoryStoreService.list();
    memoryRecords.value = [...list].sort((a, b) => {
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });

    if (!preservePage) {
      memoryPage.value = 1;
    } else {
      memoryPage.value = Math.min(memoryPage.value, memoryTotalPages.value);
      if (memoryPage.value < 1) memoryPage.value = 1;
    }
  } catch (error) {
    logger.error('[DataExportSection] 加载记忆列表失败:', error);
    memoryBrowserMessage.value = '加载记忆失败，请稍后重试。';
  } finally {
    isMemoryListLoading.value = false;
  }
}

async function openMemoryBrowser(): Promise<void> {
  isMemoryBrowserOpen.value = true;
  await refreshMemoryRecords(false);
}

function closeMemoryBrowser(): void {
  isMemoryBrowserOpen.value = false;
}

function goPrevMemoryPage(): void {
  if (memoryPage.value > 1) {
    memoryPage.value -= 1;
  }
}

function goNextMemoryPage(): void {
  if (memoryPage.value < memoryTotalPages.value) {
    memoryPage.value += 1;
  }
}

function formatMemoryTime(dateStr?: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;
  
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

async function handleDeleteMemory(memoryId: string): Promise<void> {
  const confirmed = window.confirm('确认删除这条记忆吗？');
  if (!confirmed) return;

  try {
    const removed = await memoryStoreService.remove(memoryId);
    if (!removed) {
      memoryBrowserMessage.value = '删除失败：未找到对应记忆。';
      return;
    }
    memoryBrowserMessage.value = '删除成功。';
    await refreshMemoryRecords(true);
  } catch (error) {
    logger.error('[DataExportSection] 删除记忆失败:', error);
    memoryBrowserMessage.value = '删除失败，请稍后重试。';
  }
}

async function handleMemoryImport(): Promise<void> {
  if (!memoryImportPayload.value || isMemoryImporting.value) return;

  isMemoryImporting.value = true;
  memoryImportMessage.value = '';

  try {
    if (memoryImportStrategy.value === 'preview') {
      const preview = previewMemoryLibraryImport(memoryImportPayload.value);
      memoryImportSummary.value = preview.summary;
      memoryImportMessage.value = '记忆预览完成（未写入任何数据）。';
      return;
    }

    const isOverwrite = memoryImportStrategy.value === 'overwrite';
    const confirmed = window.confirm(
      isOverwrite
        ? '将覆盖本地记忆库，确认继续吗？'
        : '将合并导入到本地记忆库，确认继续吗？'
    );
    if (!confirmed) return;

    const result = await importMemoryLibrary(
      memoryImportPayload.value,
      memoryImportStrategy.value as 'merge' | 'overwrite'
    );

    memoryImportSummary.value = result.summary;
    if (result.applied) {
      memoryImportMessage.value = `记忆导入完成（策略: ${result.strategy}）。`;
      if (isMemoryBrowserOpen.value) {
        await refreshMemoryRecords(true);
      }
    } else if (result.warnings.length > 0) {
      memoryImportMessage.value = `记忆导入未执行：${result.warnings.join('；')}`;
    } else {
      memoryImportMessage.value = '记忆导入未执行。';
    }
  } catch (error) {
    logger.error('[DataExportSection] 记忆导入失败:', error);
    alert('记忆导入失败，请检查 JSON 格式或稍后重试。');
  } finally {
    isMemoryImporting.value = false;
  }
}
</script>
