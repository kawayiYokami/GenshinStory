<template>
  <div v-if="visible && items.length > 0" class="reference-dropdown">
        <ul>
          <li
            v-for="(item, index) in items"
            :key="item.id"
            :class="['reference-item', { active: index === activeIndex }]"
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
ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.item-name {
  font-weight: 500;
}

li.active .item-name {
  font-weight: bold;
}
</style>