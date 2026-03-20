export { default as ItemCard } from './ItemCard.vue';

// 类型定义
export interface Item {
  id: number | string;
  name: string;
  type: string;
  path: string;
  score?: number;
  rarity?: number;
  category?: string;
}
