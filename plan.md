# UI架构升级执行方案 V1.0

**版本:** 1.0  
**状态:** **待审核**  
**制定人:** 架构规划师

---

## 1. 愿景与目标 (Vision & Goal)

本次 UI 架构升级旨在将项目前端从现有实现，演进为一套由 **Tailwind CSS (基础) + DaisyUI (美学) + Headless UI (行为)** 驱动的、三位一体的现代化分层架构。

**核心目标:**
- **提升开发者体验 (DX)**: 简化样式管理，降低心智负担，统一开发模式。
- **增强可访问性 (A11y)**: 借助 Headless UI，构建符合 WCAG 标准的、专业级的无障碍组件。
- **提高代码质量与可维护性**: 实现样式、行为与业务逻辑的彻底分离。
- **加速功能迭代**: 通过标准化的组件体系和高效的样式工具，更快地响应业务需求。

## 2. 核心架构 (Core Architecture)

我们将采用如下图所示的三层分层架构，各层职责明确，协同工作：

```mermaid
graph TD;
    subgraph "前端组件架构"
        A[<b>Tailwind CSS v4</b><br/>原子化CSS工具层<br/><i>Foundation</i>] --> B;
        A --> C;
        B[<b>DaisyUI v5</b><br/>美学与主题层<br/><i>Aesthetics & Theme</i>] --> D{Vue Component};
        C[<b>@headlessui/vue</b><br/>行为与逻辑层<br/><i>Behavior & Logic</i>] --> D;
    end

    style A fill:#06B6D4,stroke:#0891B2,color:#fff
    style B fill:#6366F1,stroke:#4F46E5,color:#fff
    style C fill:#F59E0B,stroke:#D97706,color:#fff
    style D fill:#10B981,stroke:#059669,color:#fff
```

| 框架 | 解决的问题 | 扮演的角色 |
| :--- | :--- | :--- |
| **`@headlessui/vue`** | “这个组件**如何工作**？” (交互逻辑、状态管理、键盘导航、可访问性) | **大脑和骨骼 (Brain & Skeleton)** |
| **DaisyUI** | “这个组件**看起来什么样**？” (颜色、尺寸、圆角、动画、主题) | **皮肤和肌肉 (Skin & Muscles)** |
| **Tailwind CSS** | “如何构建这一切？” (提供构建上述两层所需的基础原子样式) | **细胞 (Cells)** |

## 3. 执行路线图 (Execution Roadmap)

我们将分五个阶段执行此次升级，以确保过程平稳、风险可控。

---

### **Phase 0: 基础设施搭建 (Infrastructure Setup)**
*此阶段旨在完成所有必要依赖的安装与配置，为后续组件迁移铺平道路。*

- [ ] **安装核心依赖**:
  ```bash
  npm install --save-dev tailwindcss@latest @tailwindcss/vite@latest
  npm install @headlessui/vue@latest @headlessui/tailwindcss daisyui@latest
  ```
- [ ] **配置 Vite**: 更新 [`vite.config.ts`](web/docs-site/vite.config.ts:1) 以集成 `@tailwindcss/vite` 插件，确保最佳性能。
  ```typescript
  // vite.config.ts
  import { defineConfig } from "vite";
  import tailwindcss from "@tailwindcss/vite";
  import vue from "@vitejs/plugin-vue";

  export default defineConfig({
    plugins: [tailwindcss(), vue()]
  });
  ```
- [ ] **配置主样式文件**: 在项目的全局 CSS 文件 (例如 `src/assets/css/main.css`) 中，使用 `@plugin` 指令引入 DaisyUI。
  ```css
  /* src/assets/css/main.css */
  @import "tailwindcss";
  @plugin "daisyui" {
    themes: ["m3-light", "m3-dark", "genshin-light"]; // 根据项目需求配置主题
  }
  ```
- [ ] **配置 DaisyUI 前缀**: (可选但推荐) 在 `tailwind.config.js` (如果项目需要其他 Tailwind 配置) 或通过 `@theme` 指令设置 DaisyUI 的前缀，以避免与现有样式或 Element Plus 的类名冲突。
  ```javascript
  // tailwind.config.js
  module.exports = {
    // ...
    plugins: [
      require('daisyui'),
    ],
    daisyui: {
      prefix: "dui-", // 所有 daisyUI 组件类名都将以 dui- 开头, e.g., .dui-btn
    },
  }
  ```

---

### **Phase 1: 试点组件迁移 (Pilot Migration) - `DropdownMenu`**
*此阶段选择一个具有代表性的核心组件进行端到端迁移，以验证新架构的可行性并建立迁移模式。*

- [ ] **锁定目标**: 迁移 [`DropdownMenu.vue`](web/docs-site/src/components/ui/DropdownMenu.vue) 和 [`DropdownMenuItem.vue`](web/docs-site/src/components/ui/DropdownMenuItem.vue)。
- [ ] **重构逻辑**:
  - **移除**: 手动的 `isOpen` 状态管理、`handleClickOutside` 事件监听器。
  - **替换**: 使用 `@headlessui/vue` 的 `Menu`, `MenuButton`, `MenuItems`, `MenuItem` 组件重构其骨架和交互逻辑。
- [ ] **重构样式**:
  - **移除**: `<style scoped>` 中的自定义样式。
  - **替换**:
    - 使用 DaisyUI 的组件类 (如 `.dui-btn`, `.dui-menu`, `.rounded-box`) 为组件赋予一致的外观。
    - 使用 `@headlessui/tailwindcss` 提供的 `ui-*` 变体 (如 `ui-active:bg-base-200`) 来处理交互状态样式。

---

### **Phase 2: 核心 UI 组件迁移 (Core UI Component Migration)**
*此阶段将已验证的迁移模式推广到其他核心 UI 和表单组件。*

- [ ] **迁移导航抽屉**: [`NavigationDrawer.vue`](web/docs-site/src/components/NavigationDrawer.vue)
  - **策略**: 考虑使用 `@headlessui/vue` 的 `Dialog` 组件来处理遮罩层、焦点管理和关闭逻辑。使用 DaisyUI 的 `.dui-drawer` 相关类进行样式美化。
- [ ] **迁移模态框**: [`AgentSelectorModal.vue`](web/docs-site/src/features/agent/components/AgentSelectorModal.vue)
  - **策略**: 同样使用 `Dialog` 组件作为基础，确保无障碍访问性。
- [ ] **迁移表单组件**: [`FormInput.vue`](web/docs-site/src/components/forms/FormInput.vue), `FormSelect.vue`
  - **策略**: 使用 DaisyUI 的 `.dui-input`, `.dui-select` 等表单样式类替换现有样式，统一表单外观。

---

### **Phase 3: 复杂功能组件适配 (Complex Feature Component Adaptation)**
*此阶段处理与业务逻辑紧密耦合的复杂组件，重点在于替换样式而非重写全部逻辑。*

- [ ] **适配消息气泡**: [`MessageBubble.vue`](web/docs-site/src/features/agent/components/MessageBubble.vue)
  - **策略**: 识别并替换组件内部由 Element Plus 或自定义样式定义的 UI 元素，例如按钮、卡片、加载指示器等，改为使用 DaisyUI 类。
- [ ] **适配配置面板**: `AgentConfigPanel.vue`
  - **策略**: 重点迁移面板内的按钮、开关、下拉菜单等子组件。
- [ ] **适配主聊天视图**: [`AgentChatView.vue`](web/docs-site/src/features/agent/views/AgentChatView.vue)
  - **策略**: 确保整体布局和状态指示器（如“正在思考中...”）的样式与新的 DaisyUI 主题系统保持一致。

---

### **Phase 5: 清理与收尾 (Cleanup & Finalization)**
*此阶段旨在移除旧的技术债，完成文档更新，并正式确立新的开发规范。*

- [ ] **卸载旧依赖**:
  ```bash
  npm uninstall element-plus unplugin-auto-import unplugin-vue-components
  ```
- [ ] **代码审查**: 移除所有对已卸载库的引用 (`import`)。
- [ ] **更新文档**:
  - 更新项目 `README.md` 中的“快速开始”和依赖说明。
  - 创建一份内部的《UI 组件开发指南》，说明如何使用新的三层架构开发新组件。
- [ ] **最终测试**: 对整个应用进行回归测试，特别是主题切换和跨浏览器兼容性。

## 4. AI 辅助重构指令 (AI-Assisted Refactoring Prompt)

为了最大化效率，团队成员在进行组件迁移时，可使用以下优化的指令模板：

> **指令模板:**
> “请重构以下 Vue 3 组件文件：`[文件路径]`。
> 1.  使用 **`@headlessui/vue`** 的 `[Headless UI 组件名, e.g., Menu, Dialog]` 组件替换现有的交互逻辑实现。
> 2.  移除所有 `<style scoped>` 中的自定义样式。
> 3.  使用 **DaisyUI** 的组件类 (例如 `.dui-btn`, `.dui-card`, `.dui-menu`) 和主题颜色 (例如 `bg-primary`, `text-on-surface`) 来实现其视觉样式。
> 4.  所有交互状态的样式（如 hover, active, disabled）必须使用 `@headlessui/tailwindcss` 插件提供的 `ui-*` 变体来实现。
> 5.  请保持原有的 props 和 emits 接口不变，确保组件的外部 API 兼容性。”

## 5. 验收标准 (Definition of Done)

- [ ] 所有项目中的 Vue 组件均已遵循新的三层架构模式。
- [ ] `element-plus` 及其相关插件 (`unplugin-*`) 已从 `package.json` 中完全移除。
- [ ] 所有 UI 元素都能正确响应 DaisyUI 的主题切换（包括浅色、深色、原神主题）。
- [ ] 关键交互组件（如下拉菜单、模态框）通过了基础的无障碍测试（键盘导航、焦点管理）。
- [ ] 项目文档已更新，反映了新的技术栈和开发规范。

## 6. 风险评估与缓解措施 (Risk Assessment & Mitigation)

- **风险 1: 学习曲线**
  - **描述**: 团队成员可能不熟悉 Headless UI 的 API 或 DaisyUI 的组件类名。
  - **缓解**: 组织一次简短的技术分享会，并以 Phase 1 的 `DropdownMenu` 迁移作为官方范例。
- **风险 2: 样式细节差异**
  - **描述**: 迁移后的组件与原设计在像素级别上可能存在细微差异。
  - **缓解**: 接受细微差异。本次升级的目标是标准化和提升可维护性，而非像素级完美复刻。利用 DaisyUI 的主题定制功能进行微调。
- **风险 3: 复杂组件迁移耗时**
  - **描述**: 如 `MessageBubble` 等复杂组件的样式适配可能比预期更复杂。
  - **缓解**: 鼓励采用“渐进式替换”策略，可以暂时保留部分内部元素的旧样式，待核心功能迁移完成后再逐步优化细节。
