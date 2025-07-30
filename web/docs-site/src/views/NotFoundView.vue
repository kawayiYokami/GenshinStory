<template>
  <div class="not-found-view">
    <h1>404 - 页面未找到</h1>
    <p>您要查找的页面不存在。</p>
    <router-link to="/">返回首页</router-link>
  </div>
</template>

<style scoped>
.not-found-view {
  color: var(--m3-on-surface);
  padding: 24px;
  text-align: center;
}

.not-found-view h1 {
  font-size: 2em;
  margin-bottom: 16px;
}

.not-found-view a {
  color: var(--m3-primary);
}
</style>