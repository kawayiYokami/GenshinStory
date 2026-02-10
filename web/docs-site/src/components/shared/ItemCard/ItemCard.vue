<template>
  <div
    @click="handleClick"
    class="card card-compact shadow cursor-pointer hover:shadow-md transition-shadow"
  >
    <div class="card-body">
      <h3 class="card-title text-sm">{{ item.name }}</h3>
      <p class="text-xs text-base-content/70 mt-1">{{ item.type }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Item {
  id: number | string;
  name: string;
  type: string;
  path: string;
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

const handleClick = () => {
  emit('click', props.item);
};
</script>

<style scoped>
/* 使用DaisyUI的默认样式，无需自定义样式 */
</style>