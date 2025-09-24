<template>
  <div class="stats-indicator" :class="accent">
    <span v-if="icon" class="indicator-icon">{{ icon }}</span>
    <span class="indicator-label">{{ label }}</span>
    <span class="indicator-value">{{ value }}</span>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  icon: String,
  accent: String,
})
</script>
<style scoped>
.stats-indicator {
  background: #23262e;
  border-radius: 10px;
  box-shadow: 0 1px 4px #000a;
  padding: 1.1rem 0.7rem;
  text-align: center;
  font-size: 1.1rem;
  letter-spacing: 0.03em;
  transition: box-shadow 0.3s, background 0.3s;
  position: relative;
  overflow: hidden;
}
.stats-indicator:hover {
  box-shadow: 0 0 12px #2226, 0 2px 16px #000a;
  background: #23262e;
}
.indicator-icon {
  display: block;
  font-size: 1.7rem;
  margin-bottom: 0.3rem;
  filter: none;
}
.indicator-label {
  display: block;
  font-size: 0.95rem;
  color: #bfc4cc;
  margin-bottom: 0.2rem;
  text-shadow: none;
}
.indicator-value {
  font-size: 1.3rem;
  font-weight: bold;
  color: #e2e4e8;
  letter-spacing: 0.05em;
  transition: color 0.3s;
}
.stats-indicator.cyan .indicator-value {
  color: #7fd3e6;
}
.stats-indicator.magenta .indicator-value {
  color: #c7b7c9;
}
.stats-indicator.yellow .indicator-value {
  color: #e6e3b7;
}
.stats-indicator.green .indicator-value {
  color: #b7c9b7;
}
.stats-indicator.red .indicator-value {
  color: #c9b7b7;
}
.stats-indicator.blue .indicator-value {
  color: #b7c3c9;
}
</style>
