<template>
  <div class="curation-queue-view">
    <header class="queue-header">
      <h1>Curation Queue</h1>
      <p v-if="isLoading">Loading tasks...</p>
      <p v-if="!isLoading && error" class="error-message">{{ error }}</p>
      <p v-if="!isLoading && !error && journalGroups.length === 0">No pending curation tasks.</p>
    </header>

    <div v-if="!isLoading && !error" class="journal-groups-container">
      <div v-for="group in journalGroups" :key="group.journal_id" class="journal-group-card">
        <div class="journal-header">
          <h2>Journal Entry: {{ formatDate(group.created_at) }}</h2>
          <div class="progress-container">
            <span>{{ group.tasks.length }} pending of {{ group.total_tasks }}</span>
            <progress :value="group.total_tasks - group.tasks.length" :max="group.total_tasks" class="curation-progress"></progress>
          </div>
        </div>
        <ul class="task-list">
          <li v-for="(task, index) in group.tasks" :key="task.id" class="task-item">
            <div class="task-info">
              <div class="task-header-info">
                <span class="task-name">{{ task.name }}</span>
                <span class="task-type-badge">{{ task.entity_type.toUpperCase() }}</span>
              </div>
              <p class="task-summary">{{ task.summary_short }}</p>
            </div>
            <div class="task-actions">
              <button @click="quickAccept(group, index)" class="action-btn accept-btn" title="Quick Accept">✓</button>
              <button @click="quickReject(group, index)" class="action-btn reject-btn" title="Quick Reject">✗</button>
              <button @click="navigateToCuration(group.journal_id)" class="action-btn details-btn" title="View Details">Details</button>
            </div>
          </li>
        </ul>
        <div v-if="group.tasks.length === 0" class="card-footer">
          <button @click="submitCuration(group)" class="submit-btn">Complete Curation</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const isLoading = ref(true);
const error = ref(null);
const apiResponse = ref({ entity_journals: [], relationship_journals: [] });

const journalGroups = computed(() => {
  const entityGroups = (apiResponse.value.entity_journals || []).map(journal => ({
    journal_id: journal.journal_id,
    created_at: journal.created_at,
    total_tasks: journal.pending_entities_count,
    tasks: journal.pending_entities,
    phase: 'entities',
  }));

  const relationshipGroups = (apiResponse.value.relationship_journals || []).map(journal => ({
    journal_id: journal.journal_id,
    created_at: journal.created_at,
    total_tasks: journal.pending_relationships_count,
    tasks: journal.pending_relationships || [],
    phase: 'relationships',
  }));

  return [...entityGroups, ...relationshipGroups];
});

onMounted(() => {
  fetchCurationData();
});

async function fetchCurationData() {
  try {
    isLoading.value = true;
    error.value = null;

    // Use the full URL to your API endpoint
    const response = await fetch('http://127.0.0.1:8000/api/curation/pending');

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    (data.relationship_journals || []).forEach(journal => {
      (journal.pending_relationships || []).forEach(rel => {
        rel.name = rel.sub_type ? rel.sub_type.join(', ') : rel.relationship_type;
        rel.entity_type = rel.relationship_type;
      });
    });
    apiResponse.value = data;
  } catch (err) {
    console.error("Failed to fetch curation tasks:", err);
    error.value = `Failed to load data: ${err.message}. Make sure the API server is running on port 8000.`;
  } finally {
    isLoading.value = false;
  }
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

function navigateToCuration(journalId) {
  router.push({ name: 'CurationView', params: { journalId } });
}

async function quickAccept(group, taskIndex) {
  const task = group.tasks[taskIndex];
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/curation/${group.phase}/${group.journal_id}/${task.id}/accept`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(task)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // On success, remove from list
    group.tasks.splice(taskIndex, 1);
  } catch (err) {
    console.error("Failed to quick accept entity:", err);
    error.value = `Failed to accept '${task.name}': ${err.message}.`;
  }
}

async function quickReject(group, taskIndex) {
  const task = group.tasks[taskIndex];
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/curation/${group.phase}/${group.journal_id}/${task.id}/reject`, {
      method: 'POST'
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // On success, remove from list
    group.tasks.splice(taskIndex, 1);
  } catch (err) {
    console.error("Failed to quick reject entity:", err);
    error.value = `Failed to reject '${task.name}': ${err.message}.`;
  }
}
async function submitCuration(group) {
  console.log(`Submitting ${group.phase} curation for journal`, group.journal_id);

  try {
    isLoading.value = true;
    error.value = null;

    // Use the full URL to your API endpoint with the journalId
    const response = await fetch(`http://127.0.0.1:8000/api/curation/${group.phase}/${group.journal_id}/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Curation completed successfully:', data);

    // Remove the completed journal from the appropriate list
    if (group.phase === 'entities') {
      const groupIndex = apiResponse.value.entity_journals.findIndex(g => g.journal_id === group.journal_id);
      if (groupIndex > -1) {
        apiResponse.value.entity_journals.splice(groupIndex, 1);
      }
    } else if (group.phase === 'relationships') {
      const groupIndex = apiResponse.value.relationship_journals.findIndex(g => g.journal_id === group.journal_id);
      if (groupIndex > -1) {
        apiResponse.value.relationship_journals.splice(groupIndex, 1);
      }
    }
  } catch (err) {
    console.error("Failed to complete curation:", err);
    error.value = `Failed to complete curation: ${err.message}.`;
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.curation-queue-view {
  padding: 2rem;
  background-color: #f0f2f5;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.queue-header {
  margin-bottom: 2rem;
  text-align: center;
}

.queue-header h1 {
  font-size: 2.5rem;
  color: #333;
}

.error-message {
  color: #dc3545;
  font-weight: 500;
  background-color: #f8d7da;
  padding: 0.75rem;
  border-radius: 0.25rem;
  border: 1px solid #f5c6cb;
}

.journal-groups-container {
  max-width: 900px;
  margin: 0 auto;
}

.journal-group-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
  overflow: hidden;
}

.journal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background-color: #f7f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.journal-header h2 {
  font-size: 1.25rem;
  margin: 0;
  color: #34495e;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: #555;
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
  border-bottom: 1px solid #f0f2f5;
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
  color: #6c757d;
  margin: 0;
  padding-left: 2px; /* to align with task-name */
}

.task-name {
  font-weight: 500;
}

.task-type-badge {
  background-color: #e9ecef;
  color: #495057;
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

.accept-btn, .reject-btn {
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
</style>
