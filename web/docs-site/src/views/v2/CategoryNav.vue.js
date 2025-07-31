import { watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAppStore } from '@/stores/app';
import { useDataStore } from '@/stores/data';
import { storeToRefs } from 'pinia';
const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const dataStore = useDataStore();
const { indexData: fullIndex } = storeToRefs(dataStore);
const categoryTranslations = {
    // HSR
    books: '书籍',
    characters: '角色',
    lightcones: '光锥',
    relics: '遗器',
    materials: '材料',
    miracles: '奇物',
    messages: '短信',
    missions: '任务',
    // GI
    quest: '任务',
    questchapter: '任务',
    character: '角色',
    weapon: '武器',
    relicset: '圣遗物',
    material: '材料',
    book: '书籍',
    readable: '读物'
};
const categories = computed(() => {
    if (!fullIndex.value.length)
        return [];
    const categoryNames = new Set();
    fullIndex.value.forEach(item => {
        // Extract top-level category (e.g., "Weapon" from "Weapon/Sword")
        const topLevelCategory = item.type.split('/')[0];
        categoryNames.add(topLevelCategory);
    });
    return Array.from(categoryNames).map(name => ({
        name: categoryTranslations[name.toLowerCase()] || name,
        path: name
    }));
});
watch(() => appStore.currentGame, (newGame) => {
    if (newGame) {
        dataStore.fetchIndex(newGame);
    }
}, { immediate: true });
function getNavPath(type, payload) {
    const game = appStore.currentGame;
    if (type === 'search') {
        return `/v2/${game}/search`;
    }
    if (type === 'agent') {
        return `/v2/${game}/agent`;
    }
    if (type === 'category' && payload) {
        return `/v2/${game}/category/${payload}`;
    }
    return `/v2/${game}`;
}
function switchGame(game) {
    if (appStore.currentGame !== game) {
        appStore.setCurrentGame(game);
        router.push(`/v2/${game}/search`);
    }
}
function isActive(categoryPath) {
    const currentCategory = route.params.categoryName;
    return currentCategory === categoryPath;
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['game-switcher']} */ ;
/** @type {__VLS_StyleScopedClasses['game-switcher']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "category-nav" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "game-switcher" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.switchGame('gi');
        } },
    ...{ class: ({ active: __VLS_ctx.appStore.currentGame === 'gi' }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.switchGame('hsr');
        } },
    ...{ class: ({ active: __VLS_ctx.appStore.currentGame === 'hsr' }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({
    ...{ class: "nav-list" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({});
const __VLS_0 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    to: (__VLS_ctx.getNavPath('search')),
}));
const __VLS_2 = __VLS_1({
    to: (__VLS_ctx.getNavPath('search')),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_3.slots.default;
var __VLS_3;
__VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({});
const __VLS_4 = {}.RouterLink;
/** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
    to: (__VLS_ctx.getNavPath('agent')),
}));
const __VLS_6 = __VLS_5({
    to: (__VLS_ctx.getNavPath('agent')),
}, ...__VLS_functionalComponentArgsRest(__VLS_5));
__VLS_7.slots.default;
var __VLS_7;
for (const [cat] of __VLS_getVForSourceType((__VLS_ctx.categories))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
        key: (cat.path),
    });
    const __VLS_8 = {}.RouterLink;
    /** @type {[typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, typeof __VLS_components.RouterLink, typeof __VLS_components.routerLink, ]} */ ;
    // @ts-ignore
    const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
        to: (__VLS_ctx.getNavPath('category', cat.path)),
        ...{ class: ({ 'router-link-active': __VLS_ctx.isActive(cat.path) }) },
    }));
    const __VLS_10 = __VLS_9({
        to: (__VLS_ctx.getNavPath('category', cat.path)),
        ...{ class: ({ 'router-link-active': __VLS_ctx.isActive(cat.path) }) },
    }, ...__VLS_functionalComponentArgsRest(__VLS_9));
    __VLS_11.slots.default;
    (cat.name);
    var __VLS_11;
}
/** @type {__VLS_StyleScopedClasses['category-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['game-switcher']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['active']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-list']} */ ;
/** @type {__VLS_StyleScopedClasses['router-link-active']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            appStore: appStore,
            categories: categories,
            getNavPath: getNavPath,
            switchGame: switchGame,
            isActive: isActive,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=CategoryNav.vue.js.map