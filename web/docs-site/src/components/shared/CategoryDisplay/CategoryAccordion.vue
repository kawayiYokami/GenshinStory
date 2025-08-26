<template>
  <div class="space-y-2">
    <div
      v-for="category in categories"
      :key="category.name"
      class="collapse collapse-arrow bg-base-200 border border-base-300"
    >
      <input type="checkbox" />
      <div class="collapse-title font-semibold text-base-content">
        {{ category.name }}
        <span class="text-xs text-base-content/70 ml-2">({{ category.items.length }})</span>
      </div>
      <div class="collapse-content bg-transparent">
        <!-- 分页导航 -->
        <PaginationControls
          v-if="category.items.length > pageSize"
          :current-page="getCurrentPage(category.name)"
          :total-items="category.items.length"
          :page-size="pageSize"
          :show-debug-info="showDebugInfo"
          @change-page="(page) => changePage(category.name, page)"
        />

        <!-- 分页显示内容 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 bg-transparent">
          <ItemCard
            v-for="item in getPaginatedItems(category.name)"
            :key="item.id"
            :item="item"
            :class="'bg-base-100'"
            @click="handleItemClick"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import ItemCard from '../ItemCard/ItemCard.vue';
import PaginationControls from '../Pagination/PaginationControls.vue';

interface Item {
  id: number | string;
  name: string;
  type: string;
  path: string;
  rarity?: number;
  category?: string;
}

interface Category {
  name: string;
  items: Item[];
}

interface Props {
  items: Item[];
  groupBy: 'type' | 'category';
  pageSize?: number;
  showDebugInfo?: boolean;
}

interface Emits {
  (e: 'itemClick', item: Item): void;
}

const props = withDefaults(defineProps<Props>(), {
  pageSize: 16,
  showDebugInfo: false
});

const emit = defineEmits<Emits>();

// 分页状态管理
const currentPages = ref<Record<string, number>>({});

// 获取特定分类的当前页码
const getCurrentPage = (categoryName: string) => {
  return currentPages.value[categoryName] || 1;
};

// 按指定字段分组
const categories = computed(() => {
  const groupField = props.groupBy;
  const grouped = new Map<string, Item[]>();

  props.items.forEach(item => {
    const key = groupField === 'type' ? item.type : (item.category || '未分类');
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key)!.push(item);
  });

  return Array.from(grouped.entries())
    .map(([name, items]) => ({ name, items }))
    .sort((a, b) => a.name.localeCompare(b.name));
});

// 获取分页后的项目
const getPaginatedItems = (categoryName: string) => {
  const category = categories.value.find(c => c.name === categoryName);
  if (!category) return [];

  const page = getCurrentPage(categoryName);
  const start = (page - 1) * props.pageSize;
  const end = start + props.pageSize;
  return category.items.slice(start, end);
};

// 切换页码
const changePage = (categoryName: string, page: number) => {
  if (!currentPages.value) {
    currentPages.value = {};
  }
  currentPages.value[categoryName] = page;
};

// 处理条目点击
const handleItemClick = (item: Item) => {
  emit('itemClick', item);
};
</script>

<style scoped>
/* 使用DaisyUI的默认样式，无需自定义样式 */
</style>