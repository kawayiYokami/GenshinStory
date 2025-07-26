import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('../layouts/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('../views/HomeView.vue'),
        },
        {
          // The list view for search results
          path: 'search',
          name: 'search',
          component: () => import('../views/SearchView.vue'),
          // The detail view is now a sibling, but shares the same path prefix
          // The SearchView will have a <router-view> to display the detail
          children: [
            {
              path: 'item/:itemType/:id',
              name: 'search-detail',
              component: () => import('../views/ItemDetailView.vue'),
            },
          ]
        },
        {
          // The list view for categories
          path: 'category/:itemType',
          name: 'category',
          component: () => import('../views/ListDetailView.vue'),
           // The detail view is a child, so it can be rendered inside ListDetailView's <router-view>
          children: [
            {
              // The path is now more explicit to avoid ambiguity
              path: 'item/:detailItemType/:id',
              name: 'category-detail',
              component: () => import('../views/ItemDetailView.vue'),
            },
          ]
        },
        {
          path: 'about',
          name: 'about',
          component: () => import('../views/AboutView.vue'),
        },
      ],
    },
  ],
})

export default router
