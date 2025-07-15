<template>
  <!-- 恢复原始的、由父组件控制的 flex 布局 -->
  <ListPane
    :list="filteredList"
    :is-loading="dataStore.isLoading.list"
    :search-query="searchQuery"
    :expanded-groups="expandedGroups"
    :selected-item="selectedItem"
    @update:searchQuery="searchQuery = $event"
    @toggle-group="toggleGroup"
    @select-item="selectItem"
  />
  <DetailPane
    :selected-item-type="selectedItem?.data?.type ?? null"
    :selected-item-id="selectedItem?.data?.id?.toString() ?? null"
    :selected-item-name="selectedItem?.name ?? null"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDataStore, type ListItem } from '@/stores/data';
import { useContentStore, type PinnedItem } from '@/stores/content'; // 引入 content store
import ListPane from '@/components/ListPane.vue';
import DetailPane from '@/components/DetailPane.vue';

const route = useRoute();
const router = useRouter();
const dataStore = useDataStore();
const contentStore = useContentStore(); // 实例化 content store

const searchQuery = ref('');
const expandedGroups = ref(new Set<string>());
const selectedItem = ref<ListItem | null>(null);

const currentItemType = computed(() => route.params.itemType as string);

const listData = computed(() => dataStore.lists[currentItemType.value] || []);

const filteredList = computed(() => {
  if (!searchQuery.value) {
    return listData.value;
  }
  const lowerCaseQuery = searchQuery.value.toLowerCase();
  return listData.value
    .map(group => {
      const filteredChildren = group.children.filter(item =>
        item.name.toLowerCase().includes(lowerCaseQuery)
      );
      return { ...group, children: filteredChildren };
    })
    .filter(group => group.children.length > 0);
});

const toggleGroup = (groupName: string) => {
  if (expandedGroups.value.has(groupName)) {
    expandedGroups.value.delete(groupName);
  } else {
    expandedGroups.value.add(groupName);
  }
};

const selectItem = (item: ListItem) => {
  selectedItem.value = item;
  // 当用户从列表中选择项目时，同步更新激活的图钉状态
  // 确保传递一个完整的 PinnedItem 对象
  contentStore.setActivePinnedItem({
    type: item.data.type, // 真实的子类型
    id: item.data.id.toString(),
    name: item.name,
    navigationType: currentItemType.value, // 正确的顶级导航分类
  });
};

/**
 * 处理来自图钉栏的点击事件 (现在由 watch 调用)
 * @param {PinnedItem} pinnedItem - 被点击的图钉项
 */
const handleSelectPinnedItem = async (pinnedItem: PinnedItem) => {
  // 检查顶层导航分类是否匹配
  if (pinnedItem.navigationType !== currentItemType.value) {
    // 使用正确的 navigationType 进行路由跳转
    await router.push({ name: 'list', params: { itemType: pinnedItem.navigationType } });
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  for (const group of listData.value) {
    const foundItem = group.children.find(child =>
      child.data.id.toString() === pinnedItem.id && child.data.type === pinnedItem.type
    );
    if (foundItem) {
      selectItem(foundItem);
      if (!expandedGroups.value.has(group.groupName)) {
        toggleGroup(group.groupName);
      }
      break;
    }
  }
};

// 监视来自 PinBar 的点击信号
watch(() => contentStore.pinClickSignal, (newSignal) => {
  if (newSignal) {
    handleSelectPinnedItem(newSignal);
    // 消耗信号，防止重复触发
    contentStore.consumePinClickSignal();
  }
});


// 监视路由变化
watch(
  currentItemType,
  (newItemType) => {
    if (newItemType) {
      selectedItem.value = null;
      // 当切换主类别时，清除激活的图钉状态
      contentStore.setActivePinnedItem(null);
      expandedGroups.value.clear();
      dataStore.fetchList(newItemType);
    }
  },
  { immediate: true }
);
</script>

<!-- No styles needed, as requested -->