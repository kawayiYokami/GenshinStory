# Story 前端应用

这是 Story 项目的前端应用，一个多领域的故事管理器，提供智能化的内容浏览、搜索和交互体验。

## 技术栈标准

本项目采用以下核心技术栈：

### 核心框架
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite** - 现代前端构建工具

### UI 组件库
- **Headless UI** - 无样式的可访问 UI 组件
- **DaisyUI v5+** - 基于 Tailwind CSS 的组件库
- **Tailwind CSS v4** - 原子化 CSS 框架
- **Heroicons** - 精美的手工制作 SVG 图标库

### 开发规范

#### Vue 3 组件规范
- 使用 Vue 3 `<script setup>` 语法糖
- 采用 Composition API 编写组件逻辑
- 使用 TypeScript 进行类型定义
- 遵循单文件组件 (SFC) 结构

#### 样式规范

本项目采用 **DaisyUI v5 + Tailwind CSS v4 + Headless UI** 的现代 CSS 架构。

##### 核心原则
1. **Utility-First** 哲学：优先使用原子化工具类
2. **语义化组件**：合理使用 DaisyUI 预设组件
3. **可访问性优先**：集成 Headless UI 确保无障碍性
4. **主题系统**：基于 DaisyUI 的语义化颜色系统

##### 使用优先级
1. **DaisyUI 组件类**：`btn`, `card`, `modal`, `drawer` 等语义化组件
2. **Tailwind 工具类**：`p-4`, `flex`, `text-lg` 等原子化样式
3. **Heroicons 图标**：`@heroicons/vue` 提供的 SVG 图标组件
4. **Headless UI**：`ui-*` 前缀的可访问性功能
5. **自定义 Vue 组件**：封装复杂业务逻辑

##### 样式编写规范
```vue
<!-- 推荐：DaisyUI + Tailwind + Heroicons 组合 -->
<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title text-primary">
        <CubeIcon class="w-5 h-5" />
        {{ title }}
      </h2>
      <p class="text-base-content text-sm">{{ content }}</p>
      <div class="card-actions justify-end">
        <button class="btn btn-primary">
          <PaperAirplaneIcon class="w-4 h-4" />
          操作
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CubeIcon, PaperAirplaneIcon } from '@heroicons/vue/24/outline'
</script>
```

##### 主题颜色系统
- **语义化颜色**：`primary`, `secondary`, `accent`, `neutral`
- **状态颜色**：`success`, `warning`, `error`, `info`
- **表面颜色**：`base-100`, `base-200`, `base-300`
- **主题控制**：通过 `data-theme` 属性控制主题切换

##### 响应式断点
```css
/* 必须按从小到大顺序编写 */
class="text-sm sm:text-base md:text-lg lg:text-xl xl:text-2xl"
```

##### 禁止的反模式
- ❌ 手动重写 DaisyUI 已有组件
- ❌ 过度使用 `@apply` 指令
- ❌ 单独使用的 scoped 样式类
- ❌ 硬编码颜色值（应使用主题颜色）

#### 响应式设计
- 采用移动优先的设计原则
- 使用 Tailwind CSS 响应式修饰符
- 确保在不同设备上的良好体验

## 快速开始

### 安装依赖
```bash
npm install
```

### 开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 项目结构

```
src/
├── assets/          # 静态资源
├── components/      # 通用组件
├── composables/     # Vue 组合式函数
├── features/        # 功能模块
│   ├── agent/       # 智能代理功能
│   ├── app/         # 应用核心功能
│   ├── docs/        # 文档查看功能
│   ├── search/      # 搜索功能
│   └── settings/    # 设置功能
├── layouts/         # 布局组件
├── lib/             # 工具库
├── router/          # 路由配置
├── utils/           # 工具函数
└── views/           # 页面组件
```

## 开发指南

### 组件开发
- 使用 TypeScript 定义组件 props 和 emits
- 遵循 Vue 3 Composition API 最佳实践
- 使用 Pinia 进行状态管理
- 确保组件的可复用性和可测试性

### 样式开发
- 优先使用 DaisyUI 预设组件
- 使用 Tailwind CSS 进行样式定制
- 遵循设计系统的颜色和间距规范
- 确保深色模式的兼容性

### 无障碍性
- 使用 Headless UI 组件确保键盘导航
- 添加适当的 ARIA 属性
- 确保颜色对比度符合标准
- 支持屏幕阅读器

## 参考文档

- [Vue 3 官方文档](https://vuejs.org/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Tailwind CSS 官方文档](https://tailwindcss.com/)
- [DaisyUI 官方文档](https://daisyui.com/)
- [Headless UI 官方文档](https://headlessui.com/)
- [Heroicons 官方文档](https://heroicons.com/)

---

## ⚠️ 特别注意 (FOR AI)

**本项目使用 Tailwind CSS v4，与 v3 有重大差异：**

### 🔴 已废弃的v3配置方式
- ❌ **不再需要** `tailwind.config.js` 文件
- ❌ **不再需要** `postcss.config.js` 文件
- ❌ **不再需要** `npx tailwindcss init` 命令

### ✅ v4的正确配置方式
```javascript
// vite.config.ts - 正确的v4配置
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [vue(), tailwindcss()] // 直接使用，无需配置文件
})
```

```css
/* tailwind.css - CSS-first 配置 */
@import "tailwindcss";

@plugin "daisyui" {
  themes: all;
}

@plugin "@headlessui/tailwindcss" {
  prefix: "ui";
}
```

### 🤖 AI编程助手注意事项
- 如果AI助手寻找配置文件，说明知识库陈旧
- v4使用Oxide引擎，构建速度更快
- 所有配置通过CSS指令完成：`@plugin`, `@theme`, `@custom-variant`
- **当前项目已正确配置v4，请勿添加v3时代的配置文件**
