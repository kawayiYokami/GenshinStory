<template>
  <div class="home-container">
    <div class="domain-buttons">
      <button
        v-for="domain in domains"
        :key="domain.id"
        @click="navigateToAgent(domain.id)"
        class="domain-button"
      >
        {{ domain.name }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/features/app/stores/app'
import { useTheme } from '@/composables/useTheme'
import type { Domain } from '@/features/app/stores/app'

const router = useRouter()
const appStore = useAppStore()
const domains = ref<Domain[]>([])

// 激活主题系统
useTheme()

// 获取域列表并转换为中文名称
onMounted(async () => {
  await appStore.loadDomains()
  // 将英文名称转换为中文名称
  const domainsWithChineseNames = appStore.availableDomains.map(domain => {
    if (domain.id === 'hsr') {
      return { ...domain, name: '崩坏：星穹铁道' }
    } else if (domain.id === 'gi') {
      return { ...domain, name: '原神' }
    }
    return domain
  })
  domains.value = domainsWithChineseNames
})

// 导航到agent页面
const navigateToAgent = (domainId: string) => {
  router.push(`/domain/${domainId}/agent`)
}
</script>

<style scoped>
.home-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: var(--color-background);
  color: var(--color-base-content);
}

.domain-buttons {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  align-items: center;
}

.domain-button {
  padding: 1.5rem 3rem;
  font-size: 1.25rem;
  border: none;
  border-radius: 12px;
  background-color: var(--color-primary);
  color: var(--color-primary-content);
  cursor: pointer;
  transition: all 0.3s ease-out;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  min-width: 280px;
}

.domain-button:hover {
  background-color: var(--color-primary-container);
  color: var(--color-on-primary-container);
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.domain-button:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>