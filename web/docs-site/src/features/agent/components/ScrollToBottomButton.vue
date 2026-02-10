<template>
  <Transition
    name="scroll-button"
    appear
  >
    <button
      v-if="visible"
      @click="handleClick"
      class="scroll-to-bottom-btn bg-base-100 border border-base-300"
      :title="'滚动到底部'"
    >
      <ChevronDown class="w-6 h-6" />
    </button>
  </Transition>
</template>

<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next';

interface Props {
  visible: boolean;
}

interface Emits {
  (e: 'click'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const handleClick = () => {
  emit('click');
};
</script>

<style scoped>
.scroll-to-bottom-btn {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 3rem;
  height: 3rem;
  color: hsl(var(--bc));
  border-radius: 9999px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease-in-out;
  z-index: 40;
  top: -4rem;
  cursor: pointer;
}

/* 悬停效果 */
.scroll-to-bottom-btn:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* 过渡动画 */
.scroll-button-enter-active,
.scroll-button-leave-active {
  transition: opacity 0.2s ease-in-out;
}

.scroll-button-enter-from,
.scroll-button-leave-to {
  opacity: 0;
}

.scroll-button-enter-to,
.scroll-button-leave-from {
  opacity: 1;
}
</style>