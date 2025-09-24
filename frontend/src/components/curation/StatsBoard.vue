
<template>
  <div class="stats-board">
    <div class="stats-grid">
      <StatsIndicator label="Total Journals" :value="stats.total_journals" icon="📚" accent="cyan" />
      <StatsIndicator label="Pending Entities" :value="stats.pending_entities" icon="🧑‍💼" accent="magenta" />
      <StatsIndicator label="Pending Relationships" :value="stats.pending_relationships" icon="🔗" accent="yellow" />
      <StatsIndicator label="Completed" :value="stats.completed" icon="✅" accent="green" />
    </div>
    <div class="stats-section">
      <div class="stats-subgrid">
        <StatsIndicator label="Entities Extracted" :value="stats.entity_stats?.total_extracted ?? 0" accent="cyan" />
        <StatsIndicator label="Entities Accepted" :value="stats.entity_stats?.accepted ?? 0" accent="green" />
        <StatsIndicator label="Entities Rejected" :value="stats.entity_stats?.rejected ?? 0" accent="red" />
        <StatsIndicator label="Entities Pending" :value="stats.entity_stats?.pending ?? 0" accent="yellow" />
        <StatsIndicator label="Acceptance Rate" :value="formatRate(stats.entity_stats?.acceptance_rate)" accent="blue" />
      </div>
      <div class="stats-subgrid">
        <StatsIndicator label="Relationships Extracted" :value="stats.relationship_stats?.total_extracted ?? 0" accent="cyan" />
        <StatsIndicator label="Relationships Accepted" :value="stats.relationship_stats?.accepted ?? 0" accent="green" />
        <StatsIndicator label="Relationships Rejected" :value="stats.relationship_stats?.rejected ?? 0" accent="red" />
        <StatsIndicator label="Relationships Pending" :value="stats.relationship_stats?.pending ?? 0" accent="yellow" />
        <StatsIndicator label="Acceptance Rate" :value="formatRate(stats.relationship_stats?.acceptance_rate)" accent="blue" />
      </div>
    </div>
  </div>
</template>


<script setup>
import { computed } from 'vue'
import { useCurationStore } from '@/stores/curation'
import StatsIndicator from './StatsIndicator.vue'

const curationStore = useCurationStore()
const stats = computed(() => curationStore.stats)

function formatRate(rate) {
  return typeof rate === 'number' ? rate.toFixed(2) : '0.00'
}
</script>


// ...existing code...

<style scoped>
.stats-board {
  background: #181a20;
  border-radius: 18px;
  padding: 2.5rem 2rem;
  box-shadow: 0 0 32px #0ff2, 0 2px 16px #000a;
  font-family: 'Fira Mono', 'Menlo', 'Consolas', monospace;
  color: #eaf6fb;
  min-width: 320px;
  max-width: 900px;
  margin: 0 auto;
  animation: fadeIn 0.7s;
}
.stats-cards {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.stats-card {
  background: #23263a;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 1.2rem 1.5rem;
  min-width: 140px;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.stats-card-icon {
  font-size: 2rem;
}
.stats-card-title {
  font-size: 1rem;
  color: #00fff7;
  font-weight: 600;
}
.stats-card-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
}
.stats-section {
  margin-bottom: 1.5rem;
  text-align: left;
}
.stats-section h3 {
  margin-bottom: 0.7rem;
  color: #00fff7;
  font-size: 1.1rem;
  font-weight: 600;
}
.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1.2rem;
}
.stats-item {
  background: #23263a;
  border-radius: 8px;
  padding: 0.7rem 1.1rem;
  font-size: 1rem;
  color: #eaf6fb;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  min-width: 140px;
  margin-bottom: 0.5rem;
}
.stats-item strong {
  color: #00fff7;
  font-weight: 700;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  margin-bottom: 2.5rem;
}
.stats-section {
  display: flex;
  gap: 2rem;
  justify-content: center;
}
.stats-subgrid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1.2rem;
}

/* ...existing code... */
</style>
