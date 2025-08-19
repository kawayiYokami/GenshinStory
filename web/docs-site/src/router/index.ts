import { createRouter, createWebHashHistory } from 'vue-router';
import { useAppStore } from '@/features/app/stores/app';

const router = createRouter({
    history: createWebHashHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            // Redirect will be handled by the beforeEach guard
            name: 'root',
            component: { template: '<div>Loading...</div>' }
        },
        // --- V2 Three-Pane Layout Routes ---
        {
            path: '/domain/:domain',
            component: () => import('@/layouts/MainLayout.vue'),
            children: [
                {
                    path: 'agent',
                    name: 'v2-agent',
                    meta: { functionPane: 'AgentChatView' },
                    components: {
                        nav: () => import('@/features/navigation/components/CategoryNav.vue'),
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
                    }
                },
                {
                    path: 'category/:categoryName/:pathMatch(.*)*',
                    name: 'v2-category',
                    meta: { functionPane: 'ItemListView' },
                    components: {
                        nav: () => import('@/features/navigation/components/CategoryNav.vue'),
                        function: () => import('@/features/docs/views/ItemListView.vue'),
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
                    }
                },
                {
                    path: 'search',
                    name: 'v2-search',
                    meta: { functionPane: 'SearchViewV2' },
                    components: {
                        nav: () => import('@/features/navigation/components/CategoryNav.vue'),
                        function: () => import('@/features/search/views/SearchViewV2.vue'),
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
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

// Global navigation guard to update domain state based on URL
router.beforeEach(async (to, from, next) => {
    console.log('--- Router Navigation ---');
    console.log('From:', { path: from.path, name: from.name });
    console.log('To:', { path: to.path, name: to.name, params: to.params, meta: to.meta });

    const appStore = useAppStore();

    // Ensure domains are loaded before any route logic
    if (appStore.availableDomains.length === 0) {
        await appStore.loadDomains();
    }

    // Handle root redirect after domains are loaded
    if (to.name === 'root') {
        const defaultDomain = appStore.availableDomains[0]?.id;
        if (defaultDomain) {
            return next({ path: `/domain/${defaultDomain}/search` });
        } else {
            // Handle case where no domains are available
            return next({ name: 'NotFound' });
        }
    }

    const domain = to.params.domain as string;
    if (domain) {
        const isValidDomain = appStore.availableDomains.some(d => d.id === domain);
        if (isValidDomain) {
            if (appStore.currentDomain !== domain) {
                appStore.setCurrentDomain(domain);
            }
        } else {
            // If domain in URL is invalid, redirect to a default valid one
            const defaultDomain = appStore.availableDomains[0]?.id;
            if (defaultDomain) {
                return next({ path: `/domain/${defaultDomain}/search` });
            } else {
                return next({ name: 'NotFound' });
            }
        }
    }
    
    next();
});

export default router;