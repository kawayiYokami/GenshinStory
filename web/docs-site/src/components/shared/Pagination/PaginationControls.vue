<template>
  <div v-if="totalPages > 1" class="mb-6 flex flex-col items-center gap-4">
    <!-- 当前页码信息（调试用） -->
    <div v-if="showDebugInfo" class="text-xs text-base-content/50">
      当前页: {{ currentPage }}
    </div>

    <!-- 页码按钮 -->
    <div class="join">
      <template v-for="page in pageNumbers" :key="page">
        <button
          class="join-item btn btn-sm bg-base-100 hover:bg-base-200 border-base-300"
          :class="{
            'bg-base-200 hover:bg-base-300 border-base-400': page === currentPage,
            'btn-disabled': page === '...'
          }"
          @click="typeof page === 'number' && changePage(page)"
        >
          {{ page }}
        </button>
      </template>
    </div>

    <!-- 页面信息 -->
    <div class="text-sm text-base-content/70">
      第 {{ currentPage }} 页，共 {{ totalPages }} 页
      ({{ totalItems }} 项)
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  currentPage: number;
  totalItems: number;
  pageSize: number;
  showDebugInfo?: boolean;
}

interface Emits {
  (e: 'changePage', page: number): void;
}

const props = withDefaults(defineProps<Props>(), {
  showDebugInfo: false
});

const emit = defineEmits<Emits>();

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(props.totalItems / props.pageSize);
});

// 生成页码数组
const pageNumbers = computed(() => {
  const total = totalPages.value;
  const current = props.currentPage;
  const pages: (number | string)[] = [];

  if (total <= 7) {
    // 如果页数少于7页，全部显示
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // 总是显示第一页
    pages.push(1);

    if (current <= 4) {
      // 当前页在前4页时
      for (let i = 2; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    } else if (current >= total - 3) {
      // 当前页在后4页时
      pages.push('...');
      for (let i = total - 4; i <= total; i++) {
        pages.push(i);
      }
    } else {
      // 当前页在中间时
      pages.push('...');
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    }
  }

  return pages;
});

const changePage = (page: number) => {
  emit('changePage', page);
};
</script>

<style scoped>
/* 使用DaisyUI的默认样式，无需自定义样式 */
</style>