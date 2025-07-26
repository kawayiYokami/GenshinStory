<template>
  <div class="item-detail-view">
    <el-icon
      v-if="itemName"
      class="pin-button"
      :class="{ 'is-pinned': pinStore.isPinned(itemType, itemId) }"
      @click="handlePinClick"
    >
      <component :is="pinStore.isPinned(itemType, itemId) ? 'StarFilled' : 'Star'" />
    </el-icon>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="modern-loading-state">
       <div class="loading-content">
         <el-icon class="loading-spinner"><Loading /></el-icon>
         <h3 class="loading-title">正在加载{{ displayName }}详情...</h3>
       </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="modern-error-state">
       <div class="error-content">
         <el-icon class="error-icon"><Warning /></el-icon>
         <h3 class="error-title">{{ displayName }}加载失败</h3>
         <p class="error-description">{{ error }}</p>
         <div class="error-actions">
           <el-button type="primary" @click="loadContent" class="m3-button m3-button--filled">重试</el-button>
         </div>
       </div>
    </div>

    <!-- 内容显示 -->
    <div v-else-if="renderedContent" class="content-display">
      <div class="markdown-body" v-html="renderedContent"></div>
    </div>

    <!-- 空状态 -->
    <div v-else class="modern-empty-state">
       <div class="empty-content">
         <el-icon class="empty-icon"><DocumentDelete /></el-icon>
         <h2 class="empty-title">{{ displayName }}未找到</h2>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import 'github-markdown-css/github-markdown-light.css';
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useContentStore } from '@/stores/content';
import { usePinStore } from '@/stores/pin';
import { marked } from 'marked';
import { Loading, DocumentDelete, Warning, Star, StarFilled } from '@element-plus/icons-vue';

const route = useRoute();
const contentStore = useContentStore();
const pinStore = usePinStore();

const rawContent = ref<string | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);
const itemName = ref<string | null>(null); // We need the name for pinning

const itemType = computed(() => (route.params.detailItemType || route.params.itemType) as string);
const itemId = computed(() => route.params.id as string);
const highlightKeyword = computed(() => route.query.highlight as string | null);

const renderedContent = computed(() => {
  if (!rawContent.value) return '';
  let content = rawContent.value;
  if (highlightKeyword.value) {
    const regex = new RegExp(`(${highlightKeyword.value})`, 'gi');
    content = content.replace(regex, '<mark>$1</mark>');
  }
  return marked(content);
});

const typeDisplayNames: { [key: string]: string } = {
  quest: '任务',
  chapter: '章节',
  weapon: '武器',
  character: '角色',
  book: '书籍',
  material: '材料',
  relicset: '圣遗物套装',
};
const displayName = computed(() => typeDisplayNames[itemType.value] || '项目');

const loadContent = async () => {
  if (!itemId.value || !itemType.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    const content = await contentStore.fetchContent(itemType.value, itemId.value);
    // A bit of a hack to get the name from the first markdown h1
    const match = content.match(/^#\s*(.*)/);
    itemName.value = match ? match[1] : '未知项目';
    rawContent.value = content;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    isLoading.value = false;
  }
};

const handlePinClick = () => {
  if (itemName.value) {
    pinStore.togglePin({
      itemType: itemType.value,
      id: itemId.value,
      name: itemName.value,
      targetUrl: route.fullPath, // Save the full URL including query params
    });
  }
};

watch(() => [itemType.value, itemId.value], loadContent, { immediate: true });
</script>

<style scoped>
.pin-button {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 20px;
  color: var(--m3-on-surface-variant);
  cursor: pointer;
  z-index: 10;
}

.pin-button:hover {
  color: var(--m3-on-surface);
}

.pin-button.is-pinned {
  color: var(--el-color-warning);
}
</style>

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
  position: relative;
  flex-grow: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--m3-card-color-visible);
  border-radius: 12px;
  border: 1px solid var(--m3-border-color-soft);
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