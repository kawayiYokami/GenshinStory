/**
 * @fileoverview 应用程序路由配置文件
 * @description 定义Vue路由配置，包括路由守卫和页面导航逻辑
 * @author yokami
 */
import { createRouter, createWebHashHistory } from 'vue-router';
import { useAppStore } from '@/features/app/stores/app';

/**
 * 创建Vue路由实例
 * @description 配置路由历史模式和路由表，支持三面板布局
 */
const router = createRouter({
    history: createWebHashHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/home'  // 修改重定向目标
        },
        {
            path: '/home',
            name: 'Home',
            component: () => import('@/views/HomeView.vue')
        },
        {
            path: '/dropdown-test',
            name: 'DropdownTest',
            component: () => import('@/views/DropdownTest.vue')
        },
        {
            path: '/theme-showcase',
            name: 'ThemeShowcase',
            component: () => import('@/views/ThemeShowcase.vue')
        },
        // --- V2 三面板布局路由 ---
        {
            path: '/domain/:domain',
            component: () => import('@/layouts/MainLayout.vue'),
            children: [
                {
                    path: 'agent',
                    name: 'v2-agent',
                    meta: { functionPane: 'AgentChatView' },
                    components: {
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
                    }
                },
                {
                    path: 'category/:categoryName/:pathMatch(.*)*',
                    name: 'v2-category',
                    meta: { functionPane: 'ItemListView' },
                    components: {
                        function: () => import('@/features/docs/views/ItemListView.vue'),
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
                    }
                },
                {
                    path: 'search',
                    name: 'v2-search',
                    meta: { functionPane: 'SearchView' },
                    components: {
                        nav: () => import('@/features/navigation/components/CategoryNav.vue'),
                        function: () => import('@/features/search/views/SearchView.vue'),
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
                    }
                },
                {
                    path: 'settings',
                    name: 'v2-settings',
                    meta: { functionPane: 'SettingsView' },
                    components: {
                        nav: () => import('@/features/navigation/components/CategoryNav.vue'),
                        function: () => import('@/features/settings/views/SettingsView.vue'),
                        detail: () => import('@/features/docs/views/DetailPlaceholder.vue')
                    }
                }
            ]
        },
        // 添加404页面的捕获所有路由
        {
            path: '/:pathMatch(.*)*',
            name: 'NotFound',
            component: () => import('@/views/NotFoundView.vue'),
        }
    ]
});

/**
 * 全局导航守卫
 * @description 根据URL更新域名状态，处理域名验证和重定向
 * @param {RouteLocationNormalized} to 目标路由
 * @param {RouteLocationNormalized} from 来源路由
 * @param {NavigationGuardNext} next 下一步回调函数
 */
router.beforeEach(async (to, from, next) => {
    const appStore = useAppStore();

    // 在任何路由逻辑之前确保域名已加载
    if (appStore.availableDomains.length === 0) {
        await appStore.loadDomains();
    }

    // 在域名加载后处理根重定向
    if (to.name === 'root') {
        const defaultDomain = appStore.availableDomains[0]?.id;
        if (defaultDomain) {
            return next({ path: `/domain/${defaultDomain}/agent` });
        } else {
            // 处理没有可用域名的情况
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
            // 如果URL中的域名无效，重定向到默认的有效域名
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