/**
 * @fileoverview 环境类型声明文件
 * @description 为Vue文件和其他模块提供TypeScript类型声明
 * @author yokami
 */

/// <reference types="vite/client" />

/**
 * Vue模块声明
 * @description 为所有.vue文件提供类型支持
 */
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}