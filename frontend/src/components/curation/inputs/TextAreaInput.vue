<template>
  <div class="input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <textarea
      class="styled-textarea"
      v-bind="$attrs"
      :value="props.modelValue.value"
      rows="4"
      @input="onInput"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
const props = defineProps({
  modelValue: Object,
  label: String
});
const emit = defineEmits(['update:modelValue']);

function onInput(event) {
  emit('update:modelValue', event.target.value);
}
</script>

<style scoped>
.input-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 1.5rem;
}
.input-label {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: rgb(105, 132, 156);
  text-transform: capitalize;
}
.styled-textarea {
  font-size: 1.1rem;
  padding: 0.75rem 1rem;
  border: 1.5px solid #bfc9d1;
  border-radius: 6px;
  background: #ced0d1;
  transition: border-color 0.2s;
  resize: vertical;
}
.styled-textarea:focus {
  border-color: #007bff;
  outline: none;
  background: #e0e3e4;
}
</style>
