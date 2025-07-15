<template>
  <div class="home-view">
    <!-- 空状态 - 没有选择任务时 -->
    <div v-if="!contentStore.markdownContent && !contentStore.isLoading && !contentStore.error" class="empty-state">
      <div class="empty-content">
        <el-icon class="empty-icon"><Document /></el-icon>
        <h2 class="empty-title">欢迎使用游戏数据浏览器</h2>
        <p class="empty-description">请在左侧选择一个任务或数据项以查看详细信息</p>
        
        <div class="quick-actions">
          <el-button type="primary" :icon="Search" @click="openSearch">
            搜索数据
          </el-button>
          <el-button :icon="QuestionFilled" @click="showHelp">
            使用帮助
          </el-button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="contentStore.isLoading" class="loading-state">
      <div class="loading-content">
        <el-icon class="loading-spinner"><Loading /></el-icon>
        <h3 class="loading-title">正在加载内容...</h3>
        <p class="loading-description">请稍候，正在获取数据</p>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="contentStore.error" class="error-state">
      <el-alert
        title="内容加载失败"
        :description="contentStore.error"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />
      <div class="error-actions">
        <el-button type="primary" @click="retry">重试</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </div>

    <!-- 内容显示 -->
    <div v-else class="content-display">
      <div class="content-header">
        <div class="content-meta">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>数据浏览器</el-breadcrumb-item>
            <el-breadcrumb-item>任务</el-breadcrumb-item>
            <el-breadcrumb-item class="current-item">当前内容</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="content-actions">
          <el-button :icon="Share" size="small" text>分享</el-button>
          <el-button :icon="Download" size="small" text>导出</el-button>
          <el-button :icon="Star" size="small" text>收藏</el-button>
        </div>
      </div>

      <div class="content-body">
        <div class="content-card">
          <div 
            class="markdown-content"
            v-html="contentStore.markdownContent"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useContentStore } from '@/stores/content'
import { 
  Document, 
  Loading, 
  Search, 
  QuestionFilled,
  Share,
  Download,
  Star
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const contentStore = useContentStore()

const openSearch = () => {
  ElMessage.info('搜索功能正在开发中...')
}

const showHelp = () => {
  ElMessage.info('帮助文档正在开发中...')
}

const retry = () => {
  // 重新加载当前内容
  contentStore.error = null
  ElMessage.success('正在重新加载...')
}

const goBack = () => {
  contentStore.error = null
  contentStore.markdownContent = ''
}
</script>

<style scoped>
.home-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--m3-surface);
}

/* 状态页通用样式 */
.empty-state,
.loading-state,
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 24px;
}

.empty-content,
.loading-content {
  text-align: center;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-icon {
  font-size: 64px;
  color: var(--m3-primary);
  opacity: 0.8;
}

.empty-title,
.loading-title {
  font-size: 22px;
  font-weight: 400;
  color: var(--m3-on-surface);
}

.empty-description,
.loading-description {
  font-size: 14px;
  color: var(--m3-on-surface-variant);
  line-height: 1.5;
}

.quick-actions,
.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}

.loading-spinner {
  font-size: 48px;
  color: var(--m3-primary);
  animation: spin 1s linear infinite;
}

/* 错误状态 */
.error-alert {
  max-width: 500px;
  background-color: var(--m3-error-container);
  --el-alert-title-color: var(--m3-on-error-container);
  --el-alert-description-color: var(--m3-on-error-container);
}
.error-alert :deep(.el-alert__icon) {
  color: var(--m3-error);
}

/* 内容显示 */
.content-display {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 24px 24px 24px;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid var(--m3-outline);
  margin-bottom: 24px;
}

.content-meta :deep(.el-breadcrumb__inner) {
  color: var(--m3-on-surface-variant);
}
.content-meta :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--m3-on-surface);
  font-weight: 500;
}

.content-actions {
  display: flex;
  gap: 8px;
}
.content-actions .el-button {
  color: var(--m3-on-surface-variant);
}
.content-actions .el-button:hover {
  color: var(--m3-primary);
}

.content-body {
  flex: 1;
  overflow: auto;
}

.m3-card {
  background: var(--m3-surface-tint-layer-1);
  border-radius: 12px;
  border: 1px solid transparent;
  overflow: hidden;
}

/* Markdown 内容样式 (与 QuestDetailView 保持一致) */
.markdown-content {
  padding: 32px;
  color: var(--m3-on-surface);
  line-height: 1.7;
  font-size: 16px;
}

.markdown-content :deep(h1) {
  font-size: 32px;
  font-weight: 400;
  color: var(--m3-on-surface);
  margin: 0 0 24px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--m3-outline);
}

.markdown-content :deep(h2) {
  font-size: 24px;
  font-weight: 400;
  color: var(--m3-on-surface);
  margin: 40px 0 16px 0;
}

.markdown-content :deep(h3) {
  font-size: 20px;
  font-weight: 500;
  color: var(--m3-on-surface);
  margin: 32px 0 12px 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--m3-primary);
  background-color: var(--m3-surface-tint-layer-1);
  padding: 16px 20px;
  margin: 0 0 16px 0;
  font-style: normal;
  color: var(--m3-on-surface-variant);
  border-radius: 0 8px 8px 0;
}

.markdown-content :deep(code) {
  background-color: var(--m3-secondary-container);
  color: var(--m3-on-secondary-container);
  padding: 3px 6px;
  border-radius: 6px;
  font-size: 14px;
  font-family: 'Roboto Mono', 'Consolas', 'Courier New', monospace;
}

.markdown-content :deep(pre) {
  background-color: var(--m3-surface-tint-layer-1);
  color: var(--m3-on-surface-variant);
  padding: 20px;
  border-radius: 8px;
  margin: 0 0 16px 0;
  overflow-x: auto;
  border: 1px solid var(--m3-outline);
}

.markdown-content :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

.markdown-content :deep(a) {
  color: var(--m3-primary);
  text-decoration: none;
}
.markdown-content :deep(a):hover {
  text-decoration: underline;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 16px 0;
  border: 1px solid var(--m3-outline);
  border-radius: 8px;
  overflow: hidden;
}
.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--m3-outline);
}
.markdown-content :deep(th) {
  background: var(--m3-surface-tint-layer-1);
  font-weight: 500;
}

/* 动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
