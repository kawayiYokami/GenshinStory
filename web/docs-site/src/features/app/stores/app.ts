import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface Domain {
    id: string;
    name: string;
    description: string;
    version: string;
}

export interface Game {
    id: string;
    name: string;
    description?: string;
}

export const useAppStore = defineStore('app', () => {
    // --- State ---
    const currentDomain = ref<string | null>(null);
    const availableDomains = ref<Domain[]>([]);
    const isLoadingDomains = ref(false);
    const isCoreDataReady = ref(false); // <-- NEW: The guard state

    // --- Actions ---
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
            }
            return domains;
        } catch (error) {
            console.error('Error loading domains:', error);
            return [];
        } finally {
            isLoadingDomains.value = false;
        }
    }

    function setCurrentDomain(domainId: string) {
        const isValid = availableDomains.value.some(d => d.id === domainId);
        if (isValid) {
            currentDomain.value = domainId;
        }
        else if (availableDomains.value.length > 0) {
            const defaultDomain = availableDomains.value[0].id;
            console.warn(`Invalid domain specified: ${domainId}. Defaulting to '${defaultDomain}'.`);
            currentDomain.value = defaultDomain;
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