<template>
  <div class="input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <input
      type="range"
      min="1"
      max="10"
      class="styled-slider"
      v-bind="$attrs"
      :value="displayValue"
      @input="onInput"
    />
    <span class="slider-value">{{ displayValue }}</span>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
const props = defineProps({
  modelValue: [Object, Number, String, null],
  label: String
});
const emit = defineEmits(['update:modelValue']);

// Extract numeric value from modelValue
const displayValue = computed(() => {
  if (props.modelValue === null || props.modelValue === undefined) return 1;
  
  // If it's already a number, return it
  if (typeof props.modelValue === 'number') return props.modelValue;
  
  // If it's a string, try to parse it
  if (typeof props.modelValue === 'string') {
    const parsed = Number(props.modelValue);
    return isNaN(parsed) ? 1 : parsed;
  }
  
  // If it's an object, try to extract a numeric value
  if (typeof props.modelValue === 'object' && props.modelValue !== null) {
    // Check for common numeric properties
    if (props.modelValue.value !== undefined) return Number(props.modelValue.value);
    if (props.modelValue.intensity !== undefined) return Number(props.modelValue.intensity);
    if (props.modelValue.progress !== undefined) return Number(props.modelValue.progress);
    
    // If it has a toString method, try to parse that
    if (props.modelValue.toString) {
      const parsed = Number(props.modelValue.toString());
      return isNaN(parsed) ? 1 : parsed;
    }
  }
  
  return 1; // Default value
});

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
  background: #ced0d1;
  border-radius: 6px;
  transition: background-color 0.2s;
}
.styled-slider:focus {
  background: #e0e3e4;
  outline: none;
}
.slider-value {
  font-size: 1.1rem;
  color: #007bff;
  align-self: flex-end;
}
</style>
