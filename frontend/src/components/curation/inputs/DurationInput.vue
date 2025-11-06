<template>
  <div class="input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <input
      type="text"
      class="styled-input"
      placeholder="e.g. 2:30 or 1h 15m"
      v-bind="$attrs"
      :value="displayValue"
      @input="onInput"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
const props = defineProps({
  modelValue: [Object, String, null],
  label: String
});
const emit = defineEmits(['update:modelValue']);

// Convert timedelta object to human-readable string
function formatDuration(duration) {
  // Handle null, undefined, or empty values
  if (duration === null || duration === undefined || duration === '') return '';
  
  // If it's already a string, return it
  if (typeof duration === 'string') return duration;
  
  // If it's an object (timedelta), convert to readable format
  if (typeof duration === 'object' && duration !== null) {
    // Handle different possible formats
    if (duration.days !== undefined) {
      const days = duration.days || 0;
      const hours = Math.floor(duration.seconds / 3600) || 0;
      const minutes = Math.floor((duration.seconds % 3600) / 60) || 0;
      const seconds = duration.seconds % 60 || 0;
      
      if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
      } else if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}`;
      } else if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
      } else {
        return `${seconds}s`;
      }
    }
    
    // If it has a string representation, use that
    if (duration.toString) {
      return duration.toString();
    }
  }
  
  return '';
}

const displayValue = computed(() => {
  return formatDuration(props.modelValue);
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
