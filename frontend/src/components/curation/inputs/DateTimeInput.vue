<template>
  <div class="input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <input
      type="datetime-local"
      class="styled-input"
      v-bind="$attrs"
      :value="displayValue"
      @input="onInput"
    />
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue';
const props = defineProps({
  modelValue: [Object, String, null],
  label: String
});
const emit = defineEmits(['update:modelValue']);

// Convert datetime object to ISO string format for datetime-local input
const displayValue = computed(() => {
  if (!props.modelValue) return '';
  
  // If it's already a string, convert it to the right format
  if (typeof props.modelValue === 'string') {
    try {
      const date = new Date(props.modelValue);
      if (!isNaN(date.getTime())) {
        return date.toISOString().slice(0, 16); // Remove seconds and timezone
      }
    } catch (e) {
      // If parsing fails, return the original string
      return props.modelValue;
    }
    return props.modelValue;
  }
  
  // If it's an object (datetime), convert to ISO string
  if (typeof props.modelValue === 'object' && props.modelValue !== null) {
    // Check if it's a Date object or has date properties
    if (props.modelValue instanceof Date) {
      return props.modelValue.toISOString().slice(0, 16); // Remove seconds and timezone
    }
    
    // If it has date/time properties, try to construct ISO string
    if (props.modelValue.year !== undefined) {
      const year = props.modelValue.year || new Date().getFullYear();
      const month = String(props.modelValue.month || 1).padStart(2, '0');
      const day = String(props.modelValue.day || 1).padStart(2, '0');
      const hour = String(props.modelValue.hour || 0).padStart(2, '0');
      const minute = String(props.modelValue.minute || 0).padStart(2, '0');
      return `${year}-${month}-${day}T${hour}:${minute}`;
    }
    
    // If it has a toString method, try to parse that
    if (props.modelValue.toString) {
      try {
        const date = new Date(props.modelValue.toString());
        if (!isNaN(date.getTime())) {
          return date.toISOString().slice(0, 16);
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }
  }
  
  return '';
});

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
  background: #ced0d1;
  transition: border-color 0.2s;
}
.styled-input:focus {
  border-color: #007bff;
  outline: none;
  background: #e0e3e4;
}
</style>
