<template>
  <div class="m3-layout" :class="{ 'drawer-open': isDrawerOpen }">
    <!-- 顶部应用栏 -->
    <header class="m3-app-bar">
      <div class="title-area">
        <button class="m3-icon-button" @click="toggleDrawer">
          <el-icon><Menu /></el-icon>
        </button>
        <h1 class="m3-app-bar__title">story</h1>
      </div>
      <div class="pin-bar-container">
        <PinBar />
      </div>
    </header>

    <!-- 导航抽屉 (保持不变) -->
    <aside class="m3-nav-drawer">
      <div class="m3-nav-drawer__content" style="padding-top: 16px;">
        <ul class="m3-list">
          <li v-for="tab in navTabs" :key="tab.name" class="m3-list-item-group">
            <div
              class="m3-list-item"
              :class="{ 'm3-list-item--active': activeTab === tab.name }"
              @click="handleTabChange(tab)"
            >
              <div class="m3-list-item__leading-icon">
                <el-icon><component :is="tab.iconComponent" /></el-icon>
              </div>
              <div class="m3-list-item__headline">{{ tab.label }}</div>
            </div>
          </li>
        </ul>
      </div>
    </aside>

    <!-- 主内容区 - 只在非根路径时显示 -->
    <main v-if="$route.name !== 'home'" class="m3-main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePinStore } from '@/stores/pin';
import PinBar from '@/components/PinBar.vue';
import {
  Menu,
  Star,
  Document,
  Folder,
  Warning,
  Histogram,
  Trophy,
  ArrowRight,
  Collection,
  Box,
  MagicStick,
  Search
} from '@element-plus/icons-vue'

// 响应式数据
const isDrawerOpen = ref(true)
const activeTab = ref('quest')
const router = useRouter()
const route = useRoute()
const pinStore = usePinStore();

// 导航标签配置 (保持给抽屉使用)
const navTabs = [
  // { name: 'sample', label: '样本', iconComponent: Star }, // 隐藏样本
  { name: 'search', label: '搜索', iconComponent: Search },
  { name: 'quest', label: '任务', iconComponent: Document },
  { name: 'weapon', label: '武器', iconComponent: MagicStick },
  { name: 'character', label: '角色', iconComponent: Trophy },
  { name: 'book', label: '书籍', iconComponent: Collection },
  { name: 'material', label: '材料', iconComponent: Folder },
  { name: 'relicset', label: '圣遗物', iconComponent: Box }
].filter(tab => tab.name !== 'sample'); // 确保在任何地方都不会意外显示

// 方法
const toggleDrawer = () => {
  isDrawerOpen.value = !isDrawerOpen.value
}

const handleTabChange = (tab: any) => {
  activeTab.value = tab.name
  if (tab.name === 'search') {
    router.push({ name: 'search' })
  } else {
    router.push({ name: 'category', params: { itemType: tab.name } })
  }
}

// 生命周期
onMounted(() => {
  if (window.innerWidth < 768) {
    isDrawerOpen.value = false
  }
})

// Watch the route to keep the active tab in sync
watch(() => route.params.itemType, (newItemType) => {
  if (newItemType) {
    activeTab.value = newItemType as string;
  } else if (route.name === 'search') {
    activeTab.value = 'search';
  }
}, { immediate: true });

</script>

<style scoped>
/* 基础布局 */
.m3-layout {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "header header"
    "drawer content";
  height: 100vh;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface);
  transition: grid-template-columns 0.3s ease;
  padding: var(--m3-gap);
  gap: var(--m3-gap);
}

/* 顶部应用栏 */
.m3-app-bar {
  grid-area: header;
  display: grid;
  grid-template-columns: 168px 1fr;
  align-items: center;
  gap: var(--m3-gap);
  height: 64px;
  background-color: transparent;
}

.title-area {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  height: 100%;
  background-color: var(--m3-card-color-hidden);
  border-radius: 12px;
}

/* 恢复 PinBar 容器样式 */
.pin-bar-container {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 12px;
  background-color: var(--m3-card-color-hidden); /* 恢复为隐藏颜色 */
  border-radius: 12px;
  overflow: hidden;
}

.m3-app-bar__title {
  font-size: 22px;
  font-weight: 400;
  margin: 0;
}

/* 导航抽屉 (样式保持不变) */
.m3-nav-drawer {
  grid-area: drawer;
  width: 168px;
  background: var(--m3-card-color-visible);
  border: none;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow-y: auto;
  border: 1px solid var(--m3-border-color-soft);
}
/* Removed .m3-nav-drawer__header and related styles */
.m3-nav-drawer__content {
  padding: 0 12px;
}

/* 主内容区 (样式保持不变) */
.m3-main-content {
  grid-area: content;
  overflow: hidden;
  display: flex;
  gap: var(--m3-gap);
}

/* 抽屉关闭状态 (样式保持不变) */
.m3-layout:not(.drawer-open) .m3-nav-drawer {
  width: 0;
  border-right: none;
  transform: translateX(-100%);
}
.m3-layout:not(.drawer-open) {
  grid-template-columns: 0 1fr;
}


/* M3 列表样式 (样式保持不变) */
.m3-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.m3-list-item {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 16px;
  border-radius: 28px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: background-color 0.2s ease;
}

.m3-list-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--m3-state-layer-color);
  opacity: 0;
  transition: opacity var(--m3-transition-short);
}

.m3-list-item:hover::before {
  opacity: var(--m3-state-layer-opacity-hover);
}

.m3-list-item:active::before {
  opacity: var(--m3-state-layer-opacity-pressed);
}

.m3-list-item--active {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
  font-weight: 700;
}
.m3-list-item--active:hover::before {
    opacity: calc(var(--m3-state-layer-opacity-hover) + 0.04);
}
.m3-list-item__leading-icon {
  margin-right: 12px;
  font-size: 24px;
  display: flex;
  align-items: center;
}
.m3-list-item__headline {
  flex: 1;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.m3-list-item__trailing-icon {
  margin-left: 8px;
  transition: transform 0.2s ease;
}
.m3-list-item__trailing-icon.expanded {
  transform: rotate(90deg);
}

/* 嵌套列表 (样式保持不变) */
.m3-list-item.nested {
  height: 48px;
  padding-left: 32px;
}
.m3-list-item.leaf {
  height: 48px;
  padding-left: 48px;
}
.m3-list-submenu {
  overflow: hidden;
  transition: max-height 0.3s ease-out;
}
.submenu-status {
  padding: 16px 32px;
  color: var(--m3-on-surface-variant);
}

/* 按钮 (样式保持不变) */
.m3-icon-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--m3-on-surface-variant);
}
.m3-icon-button:hover {
  background-color: rgba(0,0,0,0.08);
}

/* 响应式设计 (样式保持不变) */
@media (max-width: 768px) {
  .m3-layout {
    grid-template-areas:
      "header header"
      "content content";
  }
  .m3-nav-drawer {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    box-shadow: 0 0 10px rgba(0,0,0,0.2);
  }
  .m3-layout.drawer-open .m3-nav-drawer {
    transform: translateX(0);
  }
  .m3-layout.drawer-open::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--m3-scrim);
    opacity: 0.4;
    z-index: 999;
  }
}
</style>