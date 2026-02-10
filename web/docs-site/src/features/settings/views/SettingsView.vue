<template>
  <div class="settings-view max-w-3xl w-full">
    <SettingsHeader />

    <!-- Domain Section -->
    <div class="card card-border bg-base-100 shadow-md mb-6">
      <div class="card-body">
        <h2 class="card-title mb-6">知识领域</h2>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="domain in domains"
            :key="domain.id"
            @click="switchDomain(domain.id)"
            class="btn btn-ghost justify-start"
            :class="[
              domain.id === appStore.currentDomain
                ? 'btn-active'
                : ''
            ]"
          >
            {{ domain.name }}
          </button>
        </div>
      </div>
    </div>

    <AIConfigSection
      :domains="domains"
      @switch-domain="switchDomain"
      @open-no-key-modal="openNoKeyModal"
    />

    <CustomInstructionsSection />
    <ThemeSection />
  </div>

  <!-- No Key Modal -->
  <dialog id="no-key-modal" class="modal">
    <div class="modal-box w-11/12 max-w-5xl">
      <h3 class="text-lg font-bold">获取免费API Key</h3>
      <div v-html="modalContent"></div>
      <div class="modal-action">
        <form method="dialog">
          <button class="btn">关闭</button>
        </form>
      </div>
    </div>
  </dialog>

</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useConfigStore } from '@/features/app/stores/config';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import { useAppStore } from '@/features/app/stores/app';
import { useThemeStore } from '@/features/app/stores/themeStore';
import type { ThemeName } from '@/features/app/stores/themeStore';
import { useResponsive } from '@/composables/useResponsive';
import promptService, { type InstructionInfo } from '@/features/agent/tools/implementations/promptService';
import SettingsHeader from '../components/SettingsHeader.vue';
import AIConfigSection from '../components/AIConfigSection.vue';
import ThemeSection from '../components/ThemeSection.vue';
import CustomInstructionsSection from '../components/CustomInstructionsSection.vue';

// Stores
const configStore = useConfigStore();
const { configs, activeConfigId, activeConfig, isFetchingModels } = storeToRefs(configStore);
const { fetchModels, addConfig, updateConfig, deleteConfig, setActiveConfig } = configStore;

const agentStore = useAgentStore();
const appStore = useAppStore();
const themeStore = useThemeStore();
const router = useRouter();

// Responsive
const { isMobile } = useResponsive();

// Local state
const isDevMode = import.meta.env.DEV;

const domains = [
  { id: 'gi', name: '原神' },
  { id: 'hsr', name: '星穹铁道' },
];

// Modal content
const modalContent = ref('');


// Load modal content
const loadModalContent = async () => {
  try {
    const response = await fetch('/prompts/no_key_modal_content.md');
    if (response.ok) {
      const text = await response.text();
      // 简单的markdown转html转换
      let html = text.replace(/^# (.*$)/gim, '<p class="py-4">$1</p>');
      html = html.replace(/^## (.*$)/gim, '<h4 class="card-title">$1</h4>');
      html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
      html = html.replace(/^(?!<[hpl]).*$/gim, '<p>$&</p>');
      html = html.replace(/<li>/g, '<ul class="list-disc pl-5"><li>').replace(/<\/li>/g, '</li></ul>');
      modalContent.value = html;
    } else {
      // Fallback content if file not found
      modalContent.value = `<p class="py-4">以下是一些获取免费API额度的地方，您可以根据需要选择：</p>
      <div class="space-y-4">
        <div class="card card-border bg-base-100">
          <div class="card-body">
            <h4 class="card-title text-info">魔塔社区</h4>
            <p>提供免费的AI API额度，支持多种模型。</p>
            <div class="card-actions justify-end">
              <a href="https://www.motacommunity.com/" target="_blank" class="btn btn-sm btn-info">访问网站</a>
            </div>
          </div>
        </div>
        <div class="card card-border bg-base-100">
          <div class="card-body">
            <h4 class="card-title text-success">硅基流动</h4>
            <p>提供AI模型API服务，支持多种Qwen模型。</p>
            <div class="card-actions justify-end">
              <a href="https://siliconflow.cn/" target="_blank" class="btn btn-sm btn-success">访问网站</a>
            </div>
          </div>
        </div>
        <div class="card card-border bg-base-100">
          <div class="card-body">
            <h4 class="card-title text-warning">OpenRouter</h4>
            <p>聚合多个AI模型提供商的服务，通常有免费额度。</p>
            <div class="card-actions justify-end">
              <a href="https://openrouter.ai/" target="_blank" class="btn btn-sm btn-warning">访问网站</a>
            </div>
          </div>
        </div>
        <div class="alert alert-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 h-6 w-6">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <div>
            <h5 class="font-bold">推荐设置</h5>
            <p>OpenRouter推荐国外使用，推荐模型<strong>deepseekv3.1</strong>、<strong>deepseekv0324</strong>。<br>
            魔塔社区推荐国内使用，推荐模型如<strong>Qwen3-235B-A22B-Instruct-2507</strong>、<strong>Qwen/Qwen3-Coder-30B-A3B-Instruct</strong>。<br>
            <strong>DeepSeek</strong>作为角色扮演模型，智谱的<strong>GLM</strong>系列模型有较多免费额度可用。</p>
          </div>
        </div>
      </div>`;
    }
  } catch (error) {
    console.error('Failed to load modal content:', error);
    // Use fallback content
    modalContent.value = `<p class="py-4">以下是一些获取免费API额度的地方，您可以根据需要选择：</p>
      <div class="space-y-4">
        <div class="card card-border bg-base-100">
          <div class="card-body">
            <h4 class="card-title text-info">魔塔社区</h4>
            <p>提供免费的AI API额度，支持多种模型。</p>
            <div class="card-actions justify-end">
              <a href="https://www.motacommunity.com/" target="_blank" class="btn btn-sm btn-info">访问网站</a>
            </div>
          </div>
        </div>
        <div class="card card-border bg-base-100">
          <div class="card-body">
            <h4 class="card-title text-success">硅基流动</h4>
            <p>提供AI模型API服务，支持多种Qwen模型。</p>
            <div class="card-actions justify-end">
              <a href="https://siliconflow.cn/" target="_blank" class="btn btn-sm btn-success">访问网站</a>
            </div>
          </div>
        </div>
        <div class="card card-border bg-base-100">
          <div class="card-body">
            <h4 class="card-title text-warning">OpenRouter</h4>
            <p>聚合多个AI模型提供商的服务，通常有免费额度。</p>
            <div class="card-actions justify-end">
              <a href="https://openrouter.ai/" target="_blank" class="btn btn-sm btn-warning">访问网站</a>
            </div>
          </div>
        </div>
        <div class="alert alert-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 h-6 w-6">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <div>
            <h5 class="font-bold">推荐设置</h5>
            <p>OpenRouter推荐国外使用，推荐模型<strong>deepseekv3.1</strong>、<strong>deepseekv0324</strong>。<br>
            魔塔社区推荐国内使用，推荐模型如<strong>Qwen3-235B-A22B-Instruct-2507</strong>、<strong>Qwen/Qwen3-Coder-30B-A3B-Instruct</strong>。<br>
            <strong>DeepSeek</strong>作为角色扮演模型，智谱的<strong>GLM</strong>系列模型有较多免费额度可用。</p>
          </div>
        </div>
      </div>`;
  }
};

// Load content on mount
onMounted(() => {
  loadModalContent();
});

// Methods
const switchDomain = (domain: string) => {
  if (appStore.currentDomain !== domain) {
    appStore.setCurrentDomain(domain);
    router.push(`/domain/${domain}/settings`);
  }
};

const openNoKeyModal = () => {
  const modal = document.getElementById('no-key-modal') as HTMLDialogElement;
  if (modal) {
    modal.showModal();
  }
};

</script>

<style scoped>

.mobile-header {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
}

/* Scrollbar hover effect - hide by default, show on hover */
:deep(.overflow-y-auto::-webkit-scrollbar) {
  width: 6px;
}

:deep(.overflow-y-auto::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.overflow-y-auto::-webkit-scrollbar-thumb) {
  background-color: transparent;
  border-radius: 3px;
  transition: background-color 0.3s ease-in-out;
}

:deep(.overflow-y-auto:hover::-webkit-scrollbar-thumb) {
  background-color: #c1c1c1;
}

/* Firefox scrollbar */
:deep(.overflow-y-auto) {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
  transition: scrollbar-color 0.3s ease-in-out;
}

:deep(.overflow-y-auto:hover) {
  scrollbar-color: #c1c1c1 transparent;
}
</style>