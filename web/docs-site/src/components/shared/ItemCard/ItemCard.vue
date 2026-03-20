<template>
  <div
    @click="handleClick"
    class="card card-compact shadow cursor-pointer hover:shadow-md transition-shadow"
  >
    <div class="card-body relative">
      <div
        v-if="showScore"
        class="absolute top-2 right-2 text-[10px] leading-none px-2 py-1 rounded-full bg-primary/10 text-primary font-semibold"
        title="搜索分数"
      >
        {{ scoreLabel }}
      </div>
      <h3 class="card-title text-sm">{{ item.name }}</h3>
      <p class="text-xs text-base-content/70 mt-1">{{ item.type }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Item {
  id: number | string;
  name: string;
  type: string;
  path: string;
  score?: number;
  rarity?: number;
  category?: string;
}

interface Props {
  item: Item;
}

interface Emits {
  (e: 'click', item: Item): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const showScore = computed(() => typeof props.item.score === 'number' && Number.isFinite(props.item.score));
const scoreLabel = computed(() => {
  if (!showScore.value) return '';
  return Number(props.item.score).toFixed(3);
});

const handleClick = () => {
  emit('click', props.item);
};
</script>

<style scoped>
/* 使用DaisyUI的默认样式，无需自定义样式 */
</style>
