<template>
  <component :is="iconComponent" class="w-6 h-6" />
</template>

<script setup>
import { computed } from 'vue';

// 导入所有需要的 Lucide icons
import {
  MessageCircle,
  Search,
  Users,
  Sparkles,
  Star,
  Box,
  BookOpen,
  FileText,
  Clock,
  ShieldCheck,
  ClipboardList,
  Lightbulb
} from 'lucide-vue-next';

const props = defineProps({
  iconName: {
    type: String,
    required: true
  }
});

// 图标名称到 Lucide 组件的映射
const iconMap = {
  // 问答/聊天图标
  'chat': MessageCircle,
  'agent': MessageCircle,
  
  // 搜索图标
  'search': Search,
  
  // 角色/用户图标
  'character': Users,
  'characters': Users,
  
  // 武器/光锥图标
  'weapon': Sparkles,
  'lightcones': Sparkles,
  
  // 圣遗物/遗器图标
  'relicset': Star,
  'relics': ShieldCheck,
  
  // 材料图标
  'material': Box,
  'materials': Box,
  
  // 书籍/文档图标
  'book': BookOpen,
  'books': BookOpen,
  'readable': FileText,
  'messages': FileText,
  
  // 任务图标
  'quest': ClipboardList,
  'missions': ClipboardList,
  
  // 其他图标
  'miracles': Lightbulb,
  'rogue_events': Star
};

const iconComponent = computed(() => {
  return iconMap[props.iconName] || Star; // 默认图标
});
</script>