<template>
  <div v-if="hasAttachments" class="flex flex-wrap gap-2">
    <div v-for="(ref, index) in attachedReferences" :key="(ref as AttachmentItem).path" class="badge badge-neutral gap-1.5 max-w-[200px]">
      <FileText class="w-4 h-4" />
      <span class="truncate">{{ (ref as AttachmentItem).name }}</span>
      <button @click="removeReference(index)" class="attachment-btn">
        <X class="w-3 h-3" />
      </button>
    </div>
    <div v-for="(image, index) in attachedImages" :key="index" class="badge badge-neutral gap-1.5">
      <Image class="w-4 h-4" />
      <span>图片 {{ index + 1 }}</span>
      <button @click="removeImage(index)" class="attachment-btn">
        <X class="w-3 h-3" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { FileText, Image, X } from 'lucide-vue-next';

interface AttachmentItem {
  path: string;
  name: string;
}

// Props
const props = defineProps({
  attachedImages: {
    type: Array,
    default: () => []
  },
  attachedReferences: {
    type: Array,
    default: () => []
  }
});

// Emits
const emit = defineEmits(['update:attachedImages', 'update:attachedReferences']);

// Computed
const hasAttachments = computed(() =>
  props.attachedImages.length > 0 || props.attachedReferences.length > 0
);

// Methods
const removeImage = (index: number) => {
  const newImages = [...props.attachedImages];
  newImages.splice(index, 1);
  emit('update:attachedImages', newImages);
};

const removeReference = (index: number) => {
  const newReferences = [...props.attachedReferences];
  newReferences.splice(index, 1);
  emit('update:attachedReferences', newReferences);
};
</script>