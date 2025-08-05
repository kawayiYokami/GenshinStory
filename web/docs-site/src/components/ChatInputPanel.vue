<template>
  <div class="input-panel">
    <div v-if="attachedReferences.length > 0" class="attachment-container">
      <div v-for="(ref, index) in attachedReferences" :key="ref.path" class="attachment-item reference-item">
        <span class="icon">📄</span>
        <span class="name">{{ ref.name }}</span>
        <button @click="removeReference(index)" class="remove-btn">&times;</button>
      </div>
    </div>
    <div v-if="attachedImages.length > 0" class="attachment-container image-preview-container">
      <div v-for="(image, index) in attachedImages" :key="index" class="attachment-item image-preview-item">
        <img :src="image" alt="Image preview" />
        <button @click="removeImage(index)" class="remove-btn">&times;</button>
      </div>
    </div>
    <div class="input-wrapper">
      <ReferenceDropdown
        ref="dropdownRef"
        :items="referenceItems"
        :visible="showDropdown"
        @select="handleReferenceSelect"
      />
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        placeholder="请输入您的问题或指令... (@ 引用, Ctrl+V 粘贴图片)"
        @keydown.enter.exact.prevent="handleKeyDown"
        @keydown.up.prevent="handleKeyDown"
        @keydown.down.prevent="handleKeyDown"
        @keydown.esc.prevent="handleKeyDown"
        @keydown.backspace="handleKeyDown"
        :disabled="isLoading"
        @paste="handlePaste"
      ></textarea>
      <button
        @click="isLoading ? stopAgent() : handleSend()"
        :disabled="!isLoading && (!modelValue.trim() && attachedImages.length === 0 && attachedReferences.length === 0)"
        :class="['send-button', { 'stop-button': isLoading }]"
        :title="isLoading ? '打断' : '发送'"
      >
        <svg v-if="isLoading" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 11L12 6L17 11M12 18V6"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import { useDataStore } from '@/stores/data';
import ReferenceDropdown from './ReferenceDropdown.vue';
import debounce from 'lodash.debounce';

const dataStore = useDataStore();

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'send', 'stop']);

const textareaRef = ref(null);
const attachedImages = ref([]);
const attachedReferences = ref([]);

// --- Reference / Mention states ---
const dropdownRef = ref(null);
const showDropdown = ref(false);
const referenceItems = ref([]);
const isProcessingReference = ref(false);
let referenceQuery = '';
let referenceStartPos = -1;


const adjustTextareaHeight = () => {
  const textarea = textareaRef.value;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }
};

const handleInput = (event) => {
  emit('update:modelValue', event.target.value);
};

const handleSend = () => {
  if (props.modelValue.trim() || attachedImages.value.length > 0 || attachedReferences.value.length > 0) {
    emit('send', {
      text: props.modelValue,
      images: attachedImages.value,
      references: attachedReferences.value,
    });
    // Clear inputs after sending
    emit('update:modelValue', '');
    attachedImages.value = [];
    attachedReferences.value = [];
  }
};

const stopAgent = () => {
  emit('stop');
};

const searchReferences = debounce(async (query) => {
  console.log(`[Debug] Debounced search triggered for query: "${query}"`);
  if (query) {
    referenceItems.value = await dataStore.searchCatalog(query);
    console.log(`[Debug] Search results for "${query}":`, referenceItems.value);
    showDropdown.value = referenceItems.value.length > 0;
  } else {
    showDropdown.value = false;
  }
}, 300);

const handleReferenceSelect = (item) => {
  // Add to attachments instead of inserting text
  if (!attachedReferences.value.some(ref => ref.path === item.path)) {
    attachedReferences.value.push(item);
  }

  // Clear the @-query from the textarea
  const text = props.modelValue;
  const newText = text.substring(0, referenceStartPos);
  emit('update:modelValue', newText);

  // Hide dropdown and reset state
  showDropdown.value = false;
  isProcessingReference.value = false;
  referenceItems.value = [];

  nextTick(() => {
    textareaRef.value.focus();
  });
};

const handleKeyDown = (event) => {
    if (showDropdown.value) {
        switch (event.key) {
            case 'ArrowUp':
                dropdownRef.value?.moveUp();
                break;
            case 'ArrowDown':
                dropdownRef.value?.moveDown();
                break;
            case 'Enter':
                event.preventDefault(); // prevent form submission
                dropdownRef.value?.selectActiveItem();
                break;
            case 'Escape':
                showDropdown.value = false;
                isProcessingReference.value = false;
                break;
            default:
                return; // let other keys pass through
        }
    } else if (event.key === 'Enter') {
        handleSend();
    } else if (event.key === 'Backspace') {
        const textarea = event.target;
        const cursorPos = textarea.selectionStart;

        // Only proceed if the cursor is at the end of the selection
        if (textarea.selectionEnd !== cursorPos) return;

        const textBefore = props.modelValue.substring(0, cursorPos);

        if (textBefore.endsWith(']]')) {
            const linkStart = textBefore.lastIndexOf('[[');
            // Ensure we found a matching start and there's no nested [[
            if (linkStart !== -1 && textBefore.substring(linkStart).indexOf(']]') === -1) {
                event.preventDefault();
                
                const textAfter = props.modelValue.substring(cursorPos);
                const newText = textBefore.substring(0, linkStart) + textAfter;
                
                emit('update:modelValue', newText);
                
                nextTick(() => {
                    textarea.focus();
                    textarea.setSelectionRange(linkStart, linkStart);
                });
            }
        }
    }
};


watch(() => props.modelValue, (newValue) => {
  nextTick(adjustTextareaHeight);

  const cursorPos = textareaRef.value.selectionStart;
  const textBeforeCursor = newValue.substring(0, cursorPos);
  
  const lastAt = textBeforeCursor.lastIndexOf('@');

  if (lastAt !== -1) {
    const query = textBeforeCursor.substring(lastAt + 1);
    
    // Check for invalid characters (like whitespace) between @ and cursor
    if (/[\s\p{P}\p{S}]/u.test(query)) {
        if (isProcessingReference.value) {
            console.log('[Debug] Invalid characters in query. Hiding dropdown.');
            showDropdown.value = false;
            isProcessingReference.value = false;
        }
    } else {
        // Valid query
        console.log('[Debug] @ pattern matched. Query:', query);
        isProcessingReference.value = true;
        referenceStartPos = lastAt;
        referenceQuery = query;
        searchReferences(referenceQuery);
    }
  } else if (isProcessingReference.value) {
    console.log('[Debug] @ pattern lost. Hiding dropdown.');
    showDropdown.value = false;
    isProcessingReference.value = false;
  }
});

onMounted(() => {
  adjustTextareaHeight();
});

const handlePaste = (event) => {
  const items = event.clipboardData.items;
  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault();
      const blob = item.getAsFile();
      const reader = new FileReader();
      reader.onload = (e) => {
        attachedImages.value.push(e.target.result);
      };
      reader.readAsDataURL(blob);
    }
  }
};

const removeImage = (index) => {
  attachedImages.value.splice(index, 1);
};

const removeReference = (index) => {
  attachedReferences.value.splice(index, 1);
};

// Expose focus method for parent component
const focus = () => {
  textareaRef.value?.focus();
};

defineExpose({
  adjustTextareaHeight,
  focus,
});

</script>

<style scoped>
.attachment-container {
  display: flex;
  gap: 8px;
  padding: 0 8px 8px;
  flex-wrap: wrap;
}
.attachment-item {
  position: relative;
  display: flex;
  align-items: center;
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  border-radius: 16px;
  padding: 4px 8px;
  font-size: 0.9em;
}
.reference-item .icon {
  margin-right: 6px;
}
.image-preview-item img {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
}
.remove-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: var(--m3-error);
  color: var(--m3-on-error);
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 14px;
  line-height: 1;
  padding: 0;
}

/* --- Input Panel --- */
.input-panel {
  display: flex;
  flex-direction: column;
  padding: 16px 8px 12px;
  border-top: 1px solid var(--m3-outline);
}
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.input-panel textarea {
  width: 100%;
  min-height: 52px;
  max-height: 200px;
  padding: 14px 52px 14px 18px;
  border-radius: 26px;
  border: 1px solid var(--m3-outline);
  background-color: var(--m3-surface);
  resize: none;
  overflow-y: auto;
  line-height: 1.6;
  font-family: inherit;
  color: var(--m3-on-surface);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-panel textarea:focus {
  outline: none;
  border-color: var(--m3-primary);
  box-shadow: 0 0 0 2px var(--m3-primary-container);
}

.input-panel textarea::-webkit-scrollbar {
  display: none;
}
.input-panel textarea {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.send-button {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--m3-primary);
  color: var(--m3-on-primary);
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: background-color 0.2s;
}
.send-button:hover {
  background-color: var(--m3-primary-container);
  color: var(--m3-on-primary-container);
}
.send-button:disabled {
  background-color: var(--m3-surface-variant);
  color: var(--m3-on-surface-variant);
  cursor: not-allowed;
}
.send-button svg {
  width: 20px;
  height: 20px;
  transform: rotate(90deg);
}
.send-button.stop-button {
  background-color: var(--m3-error);
  color: var(--m3-on-error);
}
.send-button.stop-button:hover {
  background-color: var(--m3-error-container);
  color: var(--m3-on-error-container);
}
.send-button.stop-button svg {
  transform: none; /* Reset rotation for the stop icon */
}
</style>