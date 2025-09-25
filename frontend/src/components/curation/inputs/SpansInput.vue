<template>
  <div class="spans-input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <div v-for="(span, idx) in localSpans" :key="idx" class="span-row">
      <input
        type="number"
        class="span-input"
        :min="0"
        :value="span.start"
        @input="onSpanChange(idx, 'start', $event.target.value)"
        placeholder="Start"
      />
      <span class="span-separator">-</span>
      <input
        type="number"
        class="span-input"
        :min="0"
        :value="span.end"
        @input="onSpanChange(idx, 'end', $event.target.value)"
        placeholder="End"
      />
      <span v-if="span.text" class="span-text">{{ span.text }}</span>
      <button class="remove-btn" @click="removeSpan(idx)">×</button>
    </div>
    <button class="add-btn" @click="addSpan">Add Span</button>
  </div>
</template>
<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => {}
  },
  label: String
});
const emit = defineEmits(['update:modelValue']);

const localSpans = ref(props.modelValue.value);

watch(() => props.modelValue.value, (val) => {
  localSpans.value = val;
});

function onSpanChange(idx, key, value) {
  const newVal = Number(value);
  localSpans.value[idx][key] = isNaN(newVal) ? 0 : newVal;
  emit('update:modelValue', localSpans.value.map(s => ({...s})));
}

function addSpan() {
  localSpans.value.push({ start: 0, end: 0 });
  emit('update:modelValue', localSpans.value.map(s => ({...s})));
}

function removeSpan(idx) {
  localSpans.value.splice(idx, 1);
  emit('update:modelValue', localSpans.value.map(s => ({...s})));
}
</script>

<style scoped>
.spans-input-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 1.5rem;
}
.input-label {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #34495e;
  text-transform: capitalize;
}
.span-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}
.span-input {
  width: 70px;
  font-size: 1rem;
  padding: 0.4rem 0.6rem;
  border: 1.5px solid #bfc9d1;
  border-radius: 6px;
  margin-right: 0.3rem;
  background: #f9fbfd;
  transition: border-color 0.2s;
}
.span-input:focus {
  border-color: #007bff;
  outline: none;
  background: #fff;
}
.span-separator {
  margin: 0 0.3rem;
  color: #888;
}
.add-btn {
  margin-top: 0.5rem;
  padding: 0.3rem 1rem;
  border-radius: 5px;
  border: 1px solid #ced4da;
  background-color: #f8f9fa;
  cursor: pointer;
  font-size: 0.95rem;
  color: #007bff;
  font-weight: 500;
  transition: background-color 0.2s;
}
.add-btn:hover {
  background-color: #e9ecef;
}
.remove-btn {
  margin-left: 0.5rem;
  background: #dc3545;
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.remove-btn:hover {
  background: #b52a37;
}
.span-text {
  margin-left: 0.7rem;
  font-size: 0.98rem;
  color: #333;
  background: #f3f6fa;
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
}
</style>
