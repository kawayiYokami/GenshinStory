import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { marked } from 'marked';

// 定义图钉项的接口
export interface PinnedItem {
  type: string; // 可能是子类型
  id: string;
  name: string; // 用于在UI上显示
  navigationType: string; // 新增：用于决定图标的顶级导航分类
}

export const useContentStore = defineStore('content', () => {
  // --- State ---
  const markdownContent = ref('<div style="padding: 24px; color: #888;">请在左侧选择一个项目以查看详情。</div>');
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // 新增：图钉功能的状态
  const pinnedItems = ref<PinnedItem[]>(JSON.parse(localStorage.getItem('pinnedItems') || '[]'));
  const activePinnedItem = ref<PinnedItem | null>(null); // 追踪当前激活的图钉
  const pinClickSignal = ref<PinnedItem | null>(null); // 新增：“阅后即焚”的点击信号

  // --- Getters (Computed) ---
  
  /**
   * 计算属性，用于检查当前项是否已被钉住
   * @param {string} itemType - 项目类型
   * @param {string} itemId - 项目ID
   * @returns {boolean}
   */
  const isPinned = computed(() => {
    return (itemType: string, itemId: string) =>
      pinnedItems.value.some(p => p.type === itemType && p.id === itemId);
  });


  // --- Actions ---

  /**
   * Fetches the markdown content for a specific item based on its type and ID.
   * @param {string} itemType - The type of the item (e.g., 'quest', 'weapon').
   * @param {string} itemId - The ID of the item.
   */
  async function fetchContent(itemType: string, itemId: string) {
    if (!itemType || !itemId) {
      markdownContent.value = '<div style="padding: 24px; color: #888;">无效的项目类型或ID。</div>';
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      // The backend API is unified, so we can build the URL dynamically.
      const response = await fetch(`/api/${itemType}/${itemId}/content`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const rawMarkdown = await response.text();
      markdownContent.value = await marked(rawMarkdown);

    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : `获取 ${itemType} 内容失败`;
      error.value = errorMessage;
      markdownContent.value = `<div style="padding: 24px; color: red;">${errorMessage}</div>`;
      console.error(e);
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 新增：切换项目的图钉状态
   * @param {PinnedItem} item - 要钉住或取消钉住的项目
   */
  function togglePin(item: PinnedItem) {
    const index = pinnedItems.value.findIndex(p => p.type === item.type && p.id === item.id);
    if (index > -1) {
      // 如果已存在，则移除
      pinnedItems.value.splice(index, 1);
    } else {
      // 如果不存在，则添加
      pinnedItems.value.push(item);
    }
    // 将更新后的列表保存到 localStorage
    localStorage.setItem('pinnedItems', JSON.stringify(pinnedItems.value));
  }

  /**
   * 新增：设置当前激活的图钉项
   * @param {PinnedItem | null} item - 要激活的图钉项，或 null
   */
  function setActivePinnedItem(item: PinnedItem | null) {
    activePinnedItem.value = item;
  }

  /**
   * 新增：发送一个图钉被点击的信号
   * @param {PinnedItem} item - 被点击的图钉
   */
  function notifyPinClicked(item: PinnedItem) {
    pinClickSignal.value = item;
  }

  /**
   * 新增：消耗（清空）图钉点击信号
   */
  function consumePinClickSignal() {
    pinClickSignal.value = null;
  }


  return {
    markdownContent,
    isLoading,
    error,
    pinnedItems,
    activePinnedItem,
    pinClickSignal, // 暴露信号
    isPinned,
    fetchContent,
    togglePin,
    setActivePinnedItem,
    notifyPinClicked, // 暴露新的 action
    consumePinClickSignal, // 暴露新的 action
  };
});