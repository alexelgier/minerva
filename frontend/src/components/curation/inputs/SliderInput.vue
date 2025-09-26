<template>
  <div class="input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <input
      type="range"
      min="1"
      max="10"
      class="styled-slider"
      v-bind="$attrs"
      :value="props.modelValue"
      @input="onInput"
    />
    <span class="slider-value">{{ modelValue }}</span>
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
  emit('update:modelValue', Number(event.target.value));
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
.styled-slider {
  margin: 0.5rem 0;
}
.slider-value {
  font-size: 1.1rem;
  color: #007bff;
  align-self: flex-end;
}
</style>
