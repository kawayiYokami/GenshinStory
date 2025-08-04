<template>
  <div class="input-panel">
    <div v-if="attachedImages.length > 0" class="image-preview-container">
      <div v-for="(image, index) in attachedImages" :key="index" class="image-preview-item">
        <img :src="image" alt="Image preview" />
        <button @click="removeImage(index)" class="remove-image-btn">&times;</button>
      </div>
    </div>
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        placeholder="请输入您的问题或指令... (Enter 发送, Ctrl+V 粘贴图片)"
        @keydown.enter.exact.prevent="handleSend"
        :disabled="isLoading"
        @paste="handlePaste"
      ></textarea>
      <button
        @click="isLoading ? stopAgent() : handleSend()"
        :disabled="!isLoading && (!modelValue.trim() && attachedImages.length === 0)"
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
  if (props.modelValue.trim() || attachedImages.value.length > 0) {
    emit('send', {
      text: props.modelValue,
      images: attachedImages.value
    });
    // Clear inputs after sending
    emit('update:modelValue', '');
    attachedImages.value = [];
  }
};

const stopAgent = () => {
  emit('stop');
};

watch(() => props.modelValue, () => {
  nextTick(adjustTextareaHeight);
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
.image-preview-container {
  display: flex;
  gap: 8px;
  padding: 0 8px 8px;
  flex-wrap: wrap;
}
.image-preview-item {
  position: relative;
}
.image-preview-item img {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid var(--m3-outline);
}
.remove-image-btn {
  position: absolute;
  top: -4px;
  right: -4px;
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