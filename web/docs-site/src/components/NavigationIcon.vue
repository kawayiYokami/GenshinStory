<template>
  <component :is="iconComponent" class="w-6 h-6" />
</template>

<script setup>
import { computed } from 'vue';

// 导入所有需要的 Heroicons (Outline 版本)
import {
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  UserGroupIcon,
  SparklesIcon,
  StarIcon,
  CubeIcon,
  BookOpenIcon,
  DocumentTextIcon,
  ClockIcon,
  ShieldCheckIcon,
  ClipboardDocumentListIcon,
  LightBulbIcon
} from '@heroicons/vue/24/outline';

const props = defineProps({
  iconName: {
    type: String,
    required: true
  }
});

// 图标名称到 Heroicon 组件的映射
const iconMap = {
  // 问答/聊天图标
  'chat': ChatBubbleLeftRightIcon,
  'agent': ChatBubbleLeftRightIcon,
  
  // 搜索图标
  'search': MagnifyingGlassIcon,
  
  // 角色/用户图标
  'character': UserGroupIcon,
  'characters': UserGroupIcon,
  
  // 武器/光锥图标
  'weapon': SparklesIcon,
  'lightcones': SparklesIcon,
  
  // 圣遗物/遗器图标
  'relicset': StarIcon,
  'relics': ShieldCheckIcon,
  
  // 材料图标
  'material': CubeIcon,
  'materials': CubeIcon,
  
  // 书籍/文档图标
  'book': BookOpenIcon,
  'books': BookOpenIcon,
  'readable': DocumentTextIcon,
  'messages': DocumentTextIcon,
  
  // 任务图标
  'quest': ClipboardDocumentListIcon,
  'missions': ClipboardDocumentListIcon,
  
  // 其他图标
  'miracles': LightBulbIcon,
  'rogue_events': StarIcon
};

const iconComponent = computed(() => {
  return iconMap[props.iconName] || StarIcon; // 默认图标
});
</script>