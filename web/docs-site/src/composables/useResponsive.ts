import { ref, computed, onMounted, onUnmounted } from 'vue'

export function useResponsive() {
  const windowWidth = ref(window.innerWidth)

  const isDesktop = computed(() => windowWidth.value >= 1000)
  const isTablet = computed(() => windowWidth.value >= 800 && windowWidth.value < 1000)
  const isMobile = computed(() => windowWidth.value < 800)

  const updateWidth = () => {
    windowWidth.value = window.innerWidth
  }

  onMounted(() => window.addEventListener('resize', updateWidth))
  onUnmounted(() => window.removeEventListener('resize', updateWidth))

  return { isDesktop, isTablet, isMobile, windowWidth }
}