# TypeScript 和 Vue 文件注释规范

## 引言

本文档详细说明了在项目中使用 TypeScript 和 Vue 文件时的注释规范。良好的注释习惯能够提高代码的可读性、可维护性和团队协作效率。

## TypeScript 注释规范

### 1. 文件顶部注释

每个 TypeScript 文件都应该在文件开头包含文件级注释，使用 JSDoc 格式：

```typescript
/**
 * @fileoverview 文件功能描述
 * @description 详细的文件功能说明
 * @author yokami
 */
```

### 2. 函数和方法注释

所有公开的函数和方法都应该使用 JSDoc 注释：

```typescript
/**
 * 函数功能描述
 * @param {类型} 参数名 参数描述
 * @param {类型} [可选参数] 可选参数描述
 * @return {返回类型} 返回值描述
 * @throws {异常类型} 抛出异常说明
 */
function exampleFunction(param1: string, param2?: number): string {
  // 函数实现
}
```

### 3. 类和接口注释

```typescript
/**
 * 类功能描述
 * @description 详细的类功能说明
 */
export class ExampleClass {
  /**
   * 属性描述
   */
  public propertyName: string;

  /**
   * 方法描述
   * @param {类型} 参数名 参数描述
   * @return {返回类型} 返回值描述
   */
  public methodName(param: string): string {
    // 方法实现
  }
}
```

### 4. 类型定义注释

```typescript
/**
 * 接口描述
 */
export interface ExampleInterface {
  /**
   * 属性描述
   */
  propertyName: string;
}
```

### 5. 内联注释

对于复杂的逻辑，使用单行注释 `//` 或块注释 `/* */`：

```typescript
// 单行注释：解释下一行代码的作用
const result = complexCalculation(); // 复杂的计算逻辑

/*
 * 块注释：解释复杂的算法或业务逻辑
 * 可以跨越多行
 */
```

## Vue 文件注释规范

### 1. 文件结构注释

Vue 文件应该在 `<template>`、`<script>` 和 `<style>` 标签前添加注释：

```vue
<template>
  <!-- 模板区域：负责UI渲染 -->
  <div class="example-component">
    <!-- 组件模板内容 -->
  </div>
</template>

<script setup lang="ts">
// 脚本区域：负责组件逻辑
import { ref } from 'vue';

/**
 * 组件描述
 * @description 详细的组件功能说明
 */
export default {
  name: 'ExampleComponent'
};
</script>

<style scoped>
/* 样式区域：负责组件样式 */
.example-component {
  /* 样式规则 */
}
</style>
```

### 2. 组件属性注释

```typescript
interface Props {
  /**
   * 属性描述
   */
  title: string;
  /**
   * 可选属性描述
   * @default 默认值
   */
  subtitle?: string;
}
```

### 3. 方法注释

```typescript
/**
 * 方法功能描述
 * @param {Event} event 事件对象
 */
const handleClick = (event: Event) => {
  // 方法实现
};
```

### 4. 计算属性注释

```typescript
/**
 * 计算属性描述
 * @return {string} 计算结果
 */
const computedProperty = computed(() => {
  // 计算逻辑
  return 'result';
});
```

### 5. 生命周期钩子注释

```typescript
/**
 * 组件挂载时的生命周期钩子
 */
onMounted(() => {
  // 挂载逻辑
});
```

## 最佳实践

### 1. 注释语言

- 所有注释都应该使用中文编写
- 保持注释简洁明了，避免冗余
- 使用完整的句子结构

### 2. 注释时机

- 在编写代码时同步编写注释
- 复杂逻辑必须添加注释
- API 接口和公共方法必须添加完整注释

### 3. 注释更新

- 修改代码时同步更新相关注释
- 删除代码时删除相应注释
- 重构代码时重新审视注释的准确性

### 4. 注释格式

- 使用统一的缩进和格式
- JSDoc 注释使用 `/** */` 格式
- 内联注释使用 `//` 格式
- 多行注释使用 `/* */` 格式

## 示例

### TypeScript 函数示例

```typescript
/**
 * 用户数据验证函数
 * @description 验证用户输入的数据格式和完整性
 * @param {UserInput} userData 用户输入数据
 * @return {ValidationResult} 验证结果
 * @throws {ValidationError} 当数据验证失败时抛出
 */
export function validateUserData(userData: UserInput): ValidationResult {
  // 检查必填字段
  if (!userData.username || !userData.email) {
    throw new ValidationError('用户名和邮箱为必填项');
  }

  // 验证邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(userData.email)) {
    return { isValid: false, message: '邮箱格式不正确' };
  }

  return { isValid: true, message: '验证通过' };
}
```

### Vue 组件示例

```vue
<template>
  <!-- 用户信息展示组件 -->
  <div class="user-profile">
    <h2>{{ user.name }}</h2>
    <p>{{ user.email }}</p>
  </div>
</template>

<script setup lang="ts">
/**
 * 用户信息展示组件
 * @description 用于展示用户信息，支持编辑模式
 */

// 组件属性定义
interface Props {
  /** 用户信息对象 */
  user: User;
  /** 是否处于编辑模式 */
  isEditing?: boolean;
}

const props = defineProps<Props>();

/**
 * 处理用户信息更新
 * @param {User} newUserData 新的用户信息
 */
const updateUser = (newUserData: User) => {
  // 更新用户信息的逻辑
  console.log('用户信息已更新', newUserData);
};
</script>

<style scoped>
/* 用户信息组件样式 */
.user-profile {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>
```

## 总结

遵循这些注释规范可以：
- 提高代码的可读性和可维护性
- 帮助团队成员快速理解代码功能
- 减少沟通成本，提高开发效率
- 为后续的文档生成和API文档提供基础

建议在代码审查过程中将注释规范作为检查项，确保所有代码都符合规范要求。