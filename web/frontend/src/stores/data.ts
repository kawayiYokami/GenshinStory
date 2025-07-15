import { defineStore } from 'pinia';
import { ref, markRaw } from 'vue';
import { CircleCheck, Edit, View } from '@element-plus/icons-vue';

// --- Interfaces ---

// Represents a single item within a group, now with self-describing data
export interface ListItem {
  id: number;
  name: string;
  icon?: any; // Add optional icon property
  data: {
    type: string;
    id: number;
  };
  [key: string]: any; // Allow other properties
}

// Represents a group of items in the list view
export interface ListGroup {
  groupName: string;
  children: ListItem[];
}

// --- Store Definition ---

export const useDataStore = defineStore('data', () => {
  // --- State ---

  // Stores the list data, keyed by item type (e.g., 'weapons', 'materials')
  const lists = ref<{ [itemType: string]: ListGroup[] }>({});
  
  // Stores the content of the currently selected item
  const content = ref<string | null>(null);

  // Tracks loading state for different data types
  const isLoading = ref<{ [key: string]: boolean }>({
    list: false,
    content: false,
  });

  // Tracks any errors that occur during fetching
  const error = ref<string | null>(null);

  // --- Actions ---

  /**
   * Fetches the list for a given item type from the backend.
   * Handles loading and error states.
   * @param {string} itemType - The type of item to fetch (e.g., 'weapons').
   */
  async function fetchList(itemType: string) {
    if (!itemType) return;

    isLoading.value.list = true;
    error.value = null;
    
    try {
      if (itemType === 'sample') {
        // Provide dedicated static mock data for the 'sample' category
        const sampleGroups: ListGroup[] = [
          {
            groupName: '基础组件',
            children: [
              { id: 101, name: '按钮 (Button)', icon: markRaw(CircleCheck), data: { type: 'sample', id: 101 } },
              { id: 102, name: '输入框 (Input)', icon: markRaw(Edit), data: { type: 'sample', id: 102 } },
              { id: 103, name: '卡片 (Card)', icon: markRaw(View), data: { type: 'sample', id: 103 } },
            ],
          },
          {
            groupName: '导航元素',
            children: [
              { id: 201, name: '标签页 (Tabs)', icon: markRaw(CircleCheck), data: { type: 'sample', id: 201 } },
              { id: 202, name: '面包屑 (Breadcrumbs)', icon: markRaw(CircleCheck), data: { type: 'sample', id: 202 } },
              { id: 203, name: '下拉菜单 (Dropdown)', icon: markRaw(CircleCheck), data: { type: 'sample', id: 203 } },
            ],
          },
          {
            groupName: '数据展示',
            children: [
              { id: 301, name: '表格 (Table)', icon: markRaw(View), data: { type: 'sample', id: 301 } },
              { id: 302, name: '列表 (List)', icon: markRaw(View), data: { type: 'sample', id: 302 } },
              { id: 303, name: '这是一个非常非常长的项目名称用来测试省略号和换行效果', icon: markRaw(View), data: { type: 'sample', id: 303 } },
            ],
          },
        ];
        lists.value[itemType] = sampleGroups;
      } else {
        // --- Smart Fetching Logic ---
        // Define which types should use the new `/tree` endpoint
        const treeBasedTypes = new Set(['weapon', 'character', 'relicset', 'book', 'quest', 'material']);

        if (treeBasedTypes.has(itemType)) {
          // NEW PATH: Fetch from /tree and adapt the data
          const response = await fetch(`/api/${itemType}/tree`);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Failed to fetch ${itemType} tree`);
          }
          const treeData = await response.json();
          
          // Adapt the tree structure to the ListGroup[] structure expected by ListPane
          const adaptedGroups: ListGroup[] = treeData.map((node: any) => ({
            groupName: node.label || '未分类',
            children: (node.children || []).map((child: any) => ({
              id: child.data.id,
              name: child.label,
              data: {
                type: child.data.type,
                id: child.data.id,
              }
            }))
          }));
          lists.value[itemType] = adaptedGroups;

        } else {
          // OLD PATH: Original logic for other item types
          const response = await fetch(`/api/${itemType}/list`);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Failed to fetch ${itemType} list`);
          }
          const groups: ListGroup[] = await response.json();
          lists.value[itemType] = groups;
        }
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : `An unknown error occurred while fetching the list for ${itemType}.`;
      error.value = errorMessage;
      console.error(e);
      lists.value[itemType] = []; // Clear list on error
    } finally {
      isLoading.value.list = false;
    }
  }

  /**
   * Fetches the markdown content for a specific item.
   * @param {string} itemType - The type of the item.
   * @param {number} id - The ID of the item.
   */
  async function fetchContent(itemType: string, id: number) {
    if (!itemType || !id) return;

    isLoading.value.content = true;
    error.value = null;
    content.value = null;

    try {
      if (itemType === 'sample') {
        const sampleContent = `
# 样本内容：ID ${id}

这是一个用于 **UI 展示** 的静态样本。

## 核心特性
- **响应式布局**：在不同尺寸的屏幕上都能良好显示。
- **组件化**：由独立的、可复用的 Vue 组件构成。
- **清晰的数据流**：采用 Pinia 进行集中式状态管理。

---

### 代码示例
\`\`\`typescript
// TypeScript code example
function greet(name: string): string {
  return \`Hello, \${name}!\`;
}
\`\`\`

### 引用
> “设计不仅仅是它的外观和感觉，设计是它的工作方式。” - 史蒂夫·乔布斯

这是一个完美的UI原型。
        `;
        content.value = sampleContent;
      } else {
        // Existing logic for other item types
        const response = await fetch(`/api/${itemType}/${id}/content`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to fetch content for ${itemType}/${id}`);
        }
        content.value = await response.text();
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : `An unknown error occurred while fetching content.`;
      error.value = errorMessage;
      console.error(e);
    } finally {
      isLoading.value.content = false;
    }
  }

  return {
    lists,
    content,
    isLoading,
    error,
    fetchList,
    fetchContent,
  };
});