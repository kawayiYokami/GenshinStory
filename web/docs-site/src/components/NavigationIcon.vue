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
  Lightbulb,
  Film,
  Inbox
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

  // 角色/用户图标 (GI, HSR, ZZZ)

  'character': Users,
  'characters': Users,
  'partner': Users,

  // 武器/光锥图标 (GI, HSR, ZZZ)
  'weapon': Sparkles,
  'lightcones': Sparkles,

  // 圣遗物/遗器图标 (GI, HSR)
  'relicset': Star,
  'relics': ShieldCheck,

  // 材料/道具图标 (GI, HSR, ZZZ)
  'material': Box,
  'materials': Box,
  'item': Box,

  // 书籍/文档/对话图标 (GI, HSR, ZZZ)
  'book': BookOpen,
  'books': BookOpen,
  'readable': FileText,
  'messages': FileText,
  'dialogue': MessageCircle,
  'session': ClipboardList,

  // ZZZ Specific Icons
  'hollow_item': Inbox,
  'vhs': Film,

  // 其他图标
  'miracles': Lightbulb,
  'rogue_events': Star
};

const iconComponent = computed(() => {
  return iconMap[props.iconName] || Star; // 默认图标
});
</script>