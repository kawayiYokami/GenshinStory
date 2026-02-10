<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">
    <div class="container mx-auto max-w-4xl">
      <h1 class="text-4xl font-bold text-center mb-8 text-base-content">选择你的游戏世界</h1>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="domain in domains" :key="domain.id" class="card w-full bg-base-100 shadow-sm hover:shadow-lg transition-shadow">
          <div class="card-body">
            <div class="flex justify-between items-center">
              <h2 class="card-title text-2xl">{{ domain.name }}</h2>
              <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                <GamepadIcon class="w-6 h-6 text-primary" />
              </div>
            </div>

            <p class="text-base-content/70 mt-4">与{{ domain.name }}中的角色进行智能对话，探索丰富的游戏世界</p>

            <div class="card-actions justify-end mt-6">
              <button @click="navigateToAgent(domain.id)" class="btn btn-primary btn-block">
                进入世界
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 添加一个关于区域 -->
      <div class="mt-12 text-center">
        <p class="text-base-content/60">
          由 AI 驱动的角色对话平台，支持原神、崩坏：星穹铁道等多个游戏世界
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/features/app/stores/app'
import { useTheme } from '@/composables/useTheme'
import { GamepadIcon } from 'lucide-vue-next'
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

