<template>
  <div class="item-detail-view">
    <!-- 加载状态 -->
    <div v-if="contentStore.isLoading" class="modern-loading-state">
      <div class="loading-content">
        <el-icon class="loading-spinner"><Loading /></el-icon>
        <h3 class="loading-title">正在加载{{ contentType }}详情...</h3>
        <p class="loading-description">请稍候，正在获取{{ contentType }}数据</p>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="contentStore.error" class="modern-error-state">
      <div class="error-content">
        <el-icon class="error-icon"><Warning /></el-icon>
        <h3 class="error-title">{{ contentType }}加载失败</h3>
        <p class="error-description">{{ contentStore.error }}</p>
        <div class="error-actions">
          <el-button type="primary" @click="loadContent" class="m3-button m3-button--filled">重试</el-button>
          <el-button class="m3-button m3-button--outlined">返回列表</el-button>
        </div>
      </div>
    </div>

    <!-- 内容显示 -->
    <div v-else-if="contentStore.markdownContent" class="content-display">
      <div class="markdown-body" v-html="contentStore.markdownContent"></div>
    </div>

    <!-- 空状态 -->
    <div v-else class="modern-empty-state">
      <div class="empty-content">
        <el-icon class="empty-icon"><DocumentDelete /></el-icon>
        <h2 class="empty-title">{{ contentType }}未找到</h2>
        <p class="empty-description">请检查{{ contentType }}ID是否正确，或返回列表重新选择</p>
        
        <div class="empty-actions">
          <el-button type="primary" class="m3-button m3-button--filled">返回列表</el-button>
          <el-button @click="loadContent" class="m3-button m3-button--outlined">重新加载</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import 'github-markdown-css/github-markdown-light.css';
import { watch, computed } from 'vue'
import { useContentStore } from '@/stores/content'
import {
  Loading,
  DocumentDelete,
  Warning
} from '@element-plus/icons-vue'

// The component now receives its data via props instead of the route.
const props = defineProps<{
  itemType: string;
  itemId: string;
}>();

const contentStore = useContentStore()

// A simple map to get display names for different types
const typeDisplayNames: { [key: string]: string } = {
  quest: '任务',
  chapter: '章节',
  weapon: '武器',
  character: '角色',
  book: '书籍',
  material: '材料',
  relicset: '圣遗物套装',
  relicpiece: '圣遗物散件',
  sample: '样本',
};

const contentType = computed(() => typeDisplayNames[props.itemType] || '项目');

const loadContent = async () => {
  if (props.itemId && props.itemType) {
    await contentStore.fetchContent(props.itemType, props.itemId);
  }
};

// goBack is no longer needed here, as navigation is controlled by the parent.

// Watch for changes in the props to reload content.
watch(
  () => [props.itemType, props.itemId],
  () => {
    loadContent();
  },
  { immediate: true }
);
</script>

<style>
/* We are using a global CSS library now, so we need a non-scoped style tag. */
.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 45px;
  background-color: transparent; /* Override the library's white background */
}

@media (max-width: 767px) {
  .markdown-body {
    padding: 15px;
  }
}

.item-detail-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--m3-surface);
}

/* 状态页通用样式 */
.modern-loading-state,
.modern-error-state,
.modern-empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.loading-content,
.error-content,
.empty-content {
  text-align: center;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-spinner {
  font-size: 48px;
  color: var(--m3-primary);
  animation: spin 1s linear infinite;
}

.error-icon {
  font-size: 48px;
  color: var(--m3-error);
}

.empty-icon {
  font-size: 64px;
  color: var(--m3-on-surface-variant);
  opacity: 0.5;
}

.loading-title,
.error-title,
.empty-title {
  font-size: 22px;
  font-weight: 400;
  color: var(--m3-on-surface);
  margin: 0;
}

.loading-description,
.error-description,
.empty-description {
  font-size: 14px;
  color: var(--m3-on-surface-variant);
  margin: 0;
  line-height: 1.5;
}

.error-actions,
.empty-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

/* 内容显示区域 */
.content-display {
  flex: 1;
  overflow: auto;
}

/* M3 按钮样式 (kept for consistency in error/empty states) */
.m3-button {
  --el-button-border-color: var(--m3-outline);
  --el-button-hover-border-color: var(--m3-on-surface);
  --el-button-active-border-color: var(--m3-primary);
}
.m3-button.m3-button--filled {
  --el-button-bg-color: var(--m3-primary);
  --el-button-text-color: var(--m3-on-primary);
  --el-button-hover-bg-color: color-mix(in srgb, var(--m3-primary) 92%, var(--m3-on-primary) 8%);
}
.m3-button.m3-button--outlined {
  --el-button-bg-color: transparent;
  --el-button-text-color: var(--m3-primary);
  --el-button-hover-bg-color: color-mix(in srgb, var(--m3-primary) 8%, transparent);
}

/* 动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>