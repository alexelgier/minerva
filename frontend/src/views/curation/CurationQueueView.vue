<template>
  <div class="curation-queue-view">
    <header class="queue-header">
      <h1>Curation Queue</h1>
      <p v-if="isLoading">Loading tasks...</p>
      <p v-if="!isLoading && error" class="error-message">{{ error }}</p>
      <div v-if="!isLoading && !error && journalEntries.length === 0" class="no-tasks-summary">
        <div class="empty-icon">📝</div>
        <h2 class="empty-title">No pending curation tasks</h2>
        <p class="empty-desc">All journals have been curated. Here is a summary of your progress:</p>
        <StatsBoard :stats="stats" />
      </div>
    </header>

    <div v-if="!isLoading && !error" class="journal-entries-container">
      <div v-for="journalEntry in journalEntries" :key="journalEntry.journal_id" class="journal-entry-card">
        <div class="journal-header">
          <h2>Journal Entry: {{ formatDate(journalEntry.date) }}</h2>
          <div class="progress-container">
            <span>{{ journalEntry.tasks.length }} pending tasks</span>
          </div>
        </div>
        <ul class="task-list">
          <li v-for="task in journalEntry.tasks" :key="task.id" class="task-item">
            <div class="task-info">
              <div class="task-header-info">
                <span class="task-name">{{ task.data.name }}</span>
                <span class="task-type-badge">{{ task.data.type.toUpperCase() }}</span>
              </div>
              <p class="task-summary">{{ task.data.summary_short }}</p>
            </div>
            <div class="task-actions">
              <button @click="handleCurationAction(journalEntry, task.id, 'accept')" class="action-btn accept-btn"
                title="Quick Accept">✓</button>
              <button @click="handleCurationAction(journalEntry, task.id, 'reject')" class="action-btn reject-btn"
                title="Quick Reject">✗</button>
              <button @click="navigateToCuration(journalEntry.journal_id, task.id)" class="action-btn details-btn"
                title="View Details">Details</button>
            </div>
          </li>
        </ul>
        <div v-if="journalEntry.tasks.length === 0" class="card-footer">
          <button @click="submitCuration(journalEntry)" class="submit-btn">Complete Curation</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useCurationStore } from '@/stores/curation';
import StatsBoard from '@/components/curation/StatsBoard.vue';

const router = useRouter();
const curationStore = useCurationStore();
const isLoading = computed(() => curationStore.isLoading);
const error = computed(() => curationStore.error || "");
const journalEntries = computed(() => curationStore.journalEntries || []);
const stats = computed(() => curationStore.stats || {});

onMounted(() => {
  curationStore.fetchCurationQueue();
});

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

function navigateToCuration(journalId, entityId) {
  router.push({ name: 'CurationView', params: { journalId, entityId } });
}

function handleCurationAction(journalEntry, taskuuid, action) {
  curationStore.handleCurationAction(journalEntry, taskuuid, action);
}

function submitCuration(journalEntry) {
  curationStore.submitCuration(journalEntry);
}
</script>

<style scoped>
.curation-queue-view {
  padding: 2rem;
  background-color: #101828;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.queue-header {
  margin-bottom: 2rem;
  text-align: center;
}

.queue-header h1 {
  font-size: 2.5rem;
  color: #949999;
}

.error-message {
  color: #dc3545;
  font-weight: 500;
  background-color: #f8d7da;
  padding: 0.75rem;
  border-radius: 0.25rem;
  border: 1px solid #f5c6cb;
}

.journal-entries-container {
  max-width: 900px;
  margin: 0 auto;
}

.journal-entry-card {
  background-color: #4a5565;
  color: rgb(211, 211, 211);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  overflow: hidden;
}

.journal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background-color: #1e2939;
  border-bottom: 1px solid #4a5565;
}

.journal-header h2 {
  font-size: 1.25rem;
  margin: 0;
  color: #9eb0c2;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: #b9b9b9;
}

.curation-progress {
  width: 100px;
}

.task-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #373f4b;
}

.task-item:last-child {
  border-bottom: none;
}

.task-info {
  flex-grow: 1;
  padding-right: 1rem;
}

.task-header-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.task-summary {
  font-size: 0.9rem;
  color: #b1c0cc;
  margin: 0;
  padding-left: 2px;
  /* to align with task-name */
}

.task-name {
  font-weight: 500;
}

.task-type-badge {
  background-color: #4d0d79;
  color: #d3d3d3;
  padding: 0.25em 0.6em;
  border-radius: 10px;
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
}

.task-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  border: none;
  border-radius: 5px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.details-btn {
  background-color: #007bff;
  color: white;
}

.details-btn:hover {
  background-color: #0056b3;
}

.accept-btn,
.reject-btn {
  font-weight: bold;
  font-size: 1rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.accept-btn {
  background-color: #28a745;
  color: white;
}

.accept-btn:hover {
  background-color: #218838;
}

.reject-btn {
  background-color: #dc3545;
  color: white;
}

.reject-btn:hover {
  background-color: #c82333;
}

.card-footer {
  padding: 1rem 1.5rem;
  background-color: #f7f9fa;
  text-align: right;
  border-top: 1px solid #e0e0e0;
}

.submit-btn {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.6rem 1.2rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-btn:hover {
  background-color: #0056b3;
}


.no-tasks-summary {
margin: 2rem auto;
max-width: 700px;
background: #fff;
border-radius: 16px;
box-shadow: 0 4px 16px rgba(0,0,0,0.08);
padding: 2.5rem 2rem 2rem 2rem;
text-align: center;
}
.empty-icon {
font-size: 3rem;
margin-bottom: 0.5rem;
}
.empty-title {
font-size: 2rem;
font-weight: 700;
color: #34495e;
margin-bottom: 0.5rem;
}
.empty-desc {
color: #6c757d;
margin-bottom: 2rem;
}

.no-tasks-summary {
margin: 2rem auto;
max-width: 600px;
background: #fff;
border-radius: 8px;
box-shadow: 0 2px 8px rgba(0,0,0,0.07);
padding: 2rem;
text-align: left;
}
.stats-summary h2, .stats-summary h3 {
margin-top: 1.5rem;
margin-bottom: 0.5rem;
color: #34495e;
}
.stats-summary ul {
list-style: none;
padding: 0;
margin-bottom: 1rem;
}
.stats-summary li {
margin-bottom: 0.3rem;
font-size: 1rem;
}
.stats-summary strong {
color: #007bff;
}

</style>
