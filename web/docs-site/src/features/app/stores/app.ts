/**
 * @fileoverview 应用核心状态管理模块
 * @description 管理应用全局状态，包括域管理、核心数据就绪状态等
 * @author yokami
 */

import { defineStore } from 'pinia';
import { ref } from 'vue';
import storageFacade from '@/features/app/services/storageFacade';

/**
 * 域信息接口
 */
export interface Domain {
    /** 域唯一标识符 */
    id: string;
    /** 域显示名称 */
    name: string;
    /** 域描述信息 */
    description: string;
    /** 域版本号 */
    version: string;
}

/**
 * 游戏信息接口
 */
export interface Game {
    /** 游戏唯一标识符 */
    id: string;
    /** 游戏名称 */
    name: string;
    /** 游戏描述信息（可选） */
    description?: string;
}

export const useAppStore = defineStore('app', () => {
    // --- State ---
    const currentDomain = ref<string | null>(storageFacade.getCurrentDomain());
    const availableDomains = ref<Domain[]>([]);
    const isLoadingDomains = ref(false);
    const isCoreDataReady = ref(false); // <-- NEW: The guard state

    // --- Actions ---
    /**
     * 加载可用域名列表
     * @description 从manifest文件加载域名信息，避免重复加载
     * @return {Promise<Domain[]>} 域名列表
     * @throws {Error} 当加载manifest文件失败时抛出异常
     */
    async function loadDomains(): Promise<Domain[]> {
        if (availableDomains.value.length > 0 || isLoadingDomains.value) {
            return availableDomains.value;
        }
        isLoadingDomains.value = true;
        try {
            const response = await fetch('/domains/manifest.json');
            if (!response.ok) {
                throw new Error('Failed to load domains manifest');
            }
            const domains: Domain[] = await response.json();
            availableDomains.value = domains;
            if (domains.length > 0 && !currentDomain.value) {
                currentDomain.value = domains[0].id;
                storageFacade.setCurrentDomain(currentDomain.value);
            }
            return domains;
        } catch (error) {
            console.error('Error loading domains:', error);
            return [];
        } finally {
            isLoadingDomains.value = false;
        }
    }

    /**
     * 设置当前域名
     * @description 设置当前活动的域名，如果域名无效则使用默认域名
     * @param {string} domainId 要设置的域名ID
     */
    function setCurrentDomain(domainId: string) {
        const isValid = availableDomains.value.some(d => d.id === domainId);
        if (isValid) {
            currentDomain.value = domainId;
            storageFacade.setCurrentDomain(domainId);
        }
        else if (availableDomains.value.length > 0) {
            const defaultDomain = availableDomains.value[0].id;
            console.warn(`Invalid domain specified: ${domainId}. Defaulting to '${defaultDomain}'.`);
            currentDomain.value = defaultDomain;
            storageFacade.setCurrentDomain(defaultDomain);
        } else {
            console.error("Cannot set current domain, no available domains loaded.");
        }
    }
    return {
        currentDomain,
        availableDomains,
        isLoadingDomains,
        isCoreDataReady, // <-- NEW: Expose the guard state
        loadDomains,
        setCurrentDomain,
    };
});
