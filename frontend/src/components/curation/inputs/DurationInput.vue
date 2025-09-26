<template>
  <div class="input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <input
      type="text"
      class="styled-input"
      placeholder="e.g. 2:30 or 1h 15m"
      v-bind="$attrs"
      :value="props.modelValue"
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
.styled-input {
  font-size: 1.1rem;
  padding: 0.75rem 1rem;
  border: 1.5px solid #bfc9d1;
  border-radius: 6px;
  background: #f9fbfd;
  transition: border-color 0.2s;
}
.styled-input:focus {
  border-color: #007bff;
  outline: none;
  background: #fff;
}
</style>
