<template>
  <div class="card card-border bg-base-100 shadow-md mb-6">
    <div class="card-body">
      <h2 class="card-title mb-3">数据迁移</h2>
      <p class="text-sm text-base-content/70 mb-4">
        支持导出/导入用户设置、聊天记录与记忆库占位数据。
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
            导出全部用户数据
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import logger from '@/features/app/services/loggerService';
import { useAppStore } from '@/features/app/stores/app';
import { useConfigStore } from '@/features/app/stores/config';
import { useThemeStore } from '@/features/app/stores/themeStore';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import {
  exportUserData,
  importUserData,
  previewUserDataImport,
  readUserDataImportFile,
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

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function triggerFilePicker(): void {
  fileInputRef.value?.click();
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
</script>
