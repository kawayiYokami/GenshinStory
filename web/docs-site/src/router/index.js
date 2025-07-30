import { createRouter, createWebHashHistory } from 'vue-router';
import { useAppStore } from '@/stores/app';
const router = createRouter({
    history: createWebHashHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/v2/hsr/search' // Redirect to a functional page on start
        },
        // --- V2 Three-Pane Layout Routes ---
        {
            path: '/v2/:game',
            component: () => import('@/layouts/MainLayoutV2.vue'),
            children: [
                {
                    path: 'category/:categoryName',
                    name: 'v2-category',
                    meta: { functionPane: 'ItemListView' },
                    components: {
                        nav: () => import('@/views/v2/CategoryNav.vue'),
                        function: () => import('@/views/v2/ItemListView.vue'),
                        detail: () => import('@/views/v2/DetailPlaceholder.vue')
                    }
                },
                {
                    path: 'category/:categoryName/:pathMatch(.*)*',
                    name: 'v2-detail',
                    meta: { keepFunctionPane: true },
                    components: {
                        nav: () => import('@/views/v2/CategoryNav.vue'),
                        function: () => import('@/views/v2/ItemListView.vue'),
                        detail: () => import('@/views/DetailView.vue')
                    }
                },
                {
                    path: 'search',
                    name: 'v2-search',
                    meta: { functionPane: 'SearchViewV2' },
                    components: {
                        nav: () => import('@/views/v2/CategoryNav.vue'),
                        function: () => import('@/views/v2/SearchViewV2.vue'),
                        detail: () => import('@/views/v2/DetailPlaceholder.vue')
                    }
                }
            ]
        },
        // Add a catch-all route for 404 pages
        {
            path: '/:pathMatch(.*)*',
            name: 'NotFound',
            component: () => import('@/views/NotFoundView.vue'),
        }
    ]
});
// Global navigation guard to update game state based on URL
router.beforeEach((to, from, next) => {
    const game = to.params.game;
    // It's safe to call useAppStore() here because Pinia is already installed.
    const appStore = useAppStore();
    // Basic validation for the game parameter
    if (game && ['hsr', 'gi'].includes(game)) {
        appStore.setCurrentGame(game);
    }
    next();
});
export default router;
//# sourceMappingURL=index.js.map