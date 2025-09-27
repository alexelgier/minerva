<template>
  <div class="spans-input-group">
    <label v-if="label" class="input-label">{{ label }}</label>
    <div class="spans-container">
      <div class="spans-list">
        <div v-for="(span, idx) in localSpans" :key="idx" class="span-row">
          <input
            type="number"
            class="span-input"
            :min="localSpans[idx-1] ? localSpans[idx-1].end + 1 : 0"
            :max="span.end-1"
            :value="span.start"
            @input="onSpanChange(idx, 'start', $event.target.value)"
            placeholder="Start"
          />
          <span class="span-separator">-</span>
          <!-- TODO: change undefined to max journalentry char index -->
          <input
            type="number"
            class="span-input"
            :min="span.start+1"
            :max="localSpans[idx+1] ? localSpans[idx+1].start - 1 : undefined" 
            :value="span.end"
            @input="onSpanChange(idx, 'end', $event.target.value)"
            placeholder="End"
          />  
          <span v-if="span.text" class="span-text">{{ span.text }}</span>
          <button class="remove-btn" @click="removeSpan(idx)">×</button>
        </div>
      </div>
      <div class="add-btn-container">
        <button class="add-btn" @click="addSpan">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Add Span
        </button>
      </div>
    </div>
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
  color: rgb(105, 132, 156);
  text-transform: capitalize;
}
.spans-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.spans-list {
  width: 100%;
}
.add-btn-container {
  display: flex;
  justify-content: flex-end;
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
  background: #ced0d1;
  transition: border-color 0.2s;
}
.span-input:focus {
  border-color: #007bff;
  outline: none;
  background: #e0e3e4;
}
.span-separator {
  margin: 0 0.3rem;
  color: #888;
}
.add-btn {
  padding: 0.5rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 123, 255, 0.3);
  backdrop-filter: blur(10px);
  color: white;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  width: fit-content;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.add-btn:hover {
  background: rgba(0, 123, 255, 0.5);
  border-color: rgba(0, 123, 255, 1);
  transform: translateY(-1px);
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
