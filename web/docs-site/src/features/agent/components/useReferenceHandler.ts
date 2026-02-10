import { ref } from 'vue';
import { useDataStore } from '@/features/app/stores/data';
import debounce from 'lodash.debounce';

interface ReferenceItem {
  path: string;
  name: string;
  type: string;
}

export function useReferenceHandler() {
  const dataStore = useDataStore();

  // Reference states
  const showDropdown = ref(false);
  const referenceItems = ref<ReferenceItem[]>([]);
  const isProcessingReference = ref(false);
  const referenceQuery = ref('');
  const referenceStartPos = ref(-1);

  // Reference handling
  const searchReferences = debounce(async (query: string) => {
    if (query) {
      referenceItems.value = await dataStore.searchCatalog(query);
      showDropdown.value = referenceItems.value.length > 0;
    } else {
      showDropdown.value = false;
    }
  }, 300);

  const handleReferenceSelect = (item: ReferenceItem, attachedReferences: ReferenceItem[], updateAttachedReferences: (refs: ReferenceItem[]) => void) => {
    if (!attachedReferences.some(ref => ref.path === item.path)) {
      const newReferences = [...attachedReferences, item];
      updateAttachedReferences(newReferences);
    }

    showDropdown.value = false;
    isProcessingReference.value = false;
    referenceItems.value = [];
  };

  return {
    showDropdown,
    referenceItems,
    isProcessingReference,
    referenceQuery,
    referenceStartPos,
    searchReferences,
    handleReferenceSelect
  };
}