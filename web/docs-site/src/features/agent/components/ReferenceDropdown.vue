<template>
  <div v-if="visible && items.length > 0" class="reference-dropdown">
    <ul>
      <li
        v-for="(item, index) in items"
        :key="item.id"
        :class="{ active: index === activeIndex }"
        @mousedown.prevent="selectItem(item)"
        @mouseover="activeIndex = index"
      >
        <span class="item-name">{{ item.name }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  items: {
    type: Array,
    required: true,
  },
  visible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['select']);

const activeIndex = ref(0);

watch(() => props.items, () => {
  activeIndex.value = 0;
});

const selectItem = (item) => {
  emit('select', item);
};

// Expose methods for parent component to control from keyboard events
const moveUp = () => {
  if (props.items.length === 0) return;
  activeIndex.value = (activeIndex.value - 1 + props.items.length) % props.items.length;
};

const moveDown = () => {
  if (props.items.length === 0) return;
  activeIndex.value = (activeIndex.value + 1) % props.items.length;
};

const selectActiveItem = () => {
  if (props.visible && props.items[activeIndex.value]) {
    selectItem(props.items[activeIndex.value]);
  }
};

defineExpose({
  moveUp,
  moveDown,
  selectActiveItem,
});
</script>

<style scoped>
.reference-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  width: 100%;
  max-height: 800px;
  overflow-y: auto;
  background-color: var(--m3-surface);
  border: 1px solid var(--m3-outline);
  border-radius: 12px; /* Consistent with modal */
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  margin-bottom: 8px;
  padding: 8px;
  box-sizing: border-box;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

li {
  padding: 12px;
  cursor: pointer;
  border-radius: 8px; /* Rounded corners for each item */
  transition: background-color 0.2s;
  color: var(--m3-on-surface);
  margin-bottom: 4px; /* Space between items */
}

li:last-child {
  margin-bottom: 0;
}

li:hover {
  background-color: var(--m3-surface-variant);
}

li.active {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
}

.item-name {
  font-weight: 500;
}

li.active .item-name {
  font-weight: bold;
}
</style>