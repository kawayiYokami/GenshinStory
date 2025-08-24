<template>
  <div ref="containerRef" class="virtual-list-container" :style="{ height: height + 'px' }">
    <div class="virtual-list-content" :style="{ height: totalHeight + 'px' }">
      <div
        v-for="(item, itemIndex) in visibleItems"
        :key="item.index"
        class="virtual-list-item"
        :style="{ transform: `translateY(${item.offset}px)` }"
      >
        <slot :item="item.data" :index="item.index"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface VirtualListItem<T = any> {
  data: T
  index: number
  offset: number
}

defineSlots<{
  default: (props: { item: any; index: number }) => any
}>()

const props = withDefaults(defineProps<{
  data: any[]
  itemSize?: number
  height: number
  overscan?: number
}>(), {
  itemSize: 45,
  overscan: 5
})

const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)

const totalHeight = computed(() => props.data.length * props.itemSize)

const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / props.itemSize) - props.overscan)
})

const endIndex = computed(() => {
  const visibleItems = Math.ceil(props.height / props.itemSize)
  return Math.min(
    props.data.length - 1,
    startIndex.value + visibleItems + props.overscan * 2
  )
})

const visibleItems = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value + 1).map((item, index) => ({
    data: item,
    index: startIndex.value + index,
    offset: (startIndex.value + index) * props.itemSize
  }))
})

const handleScroll = () => {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop
  }
}

onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', handleScroll)
  }
})

watch(() => props.data, () => {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop
  }
})
</script>

<style scoped>
.virtual-list-container {
  overflow-y: auto;
  position: relative;
}

.virtual-list-content {
  position: relative;
}

.virtual-list-item {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: v-bind('props.itemSize + "px"');
}
</style>