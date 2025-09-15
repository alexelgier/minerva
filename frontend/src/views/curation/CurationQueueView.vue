<template>
  <div class="curation-queue-view">
    <header class="queue-header">
      <h1>Curation Queue</h1>
      <p v-if="isLoading">Loading tasks...</p>
      <p v-if="!isLoading && journalGroups.length === 0">No pending curation tasks.</p>
    </header>

    <div v-if="!isLoading" class="journal-groups-container">
      <div v-for="group in journalGroups" :key="group.journal_id" class="journal-group-card">
        <div class="journal-header">
          <h2>Journal Entry: {{ group.journal_date }}</h2>
          <div class="progress-container">
            <span>{{ group.tasks.length }} pending of {{ group.total_tasks }}</span>
            <progress :value="group.total_tasks - group.tasks.length" :max="group.total_tasks" class="curation-progress"></progress>
          </div>
        </div>
        <ul class="task-list">
          <li v-for="(task, index) in group.tasks" :key="task.name" class="task-item">
            <div class="task-info">
              <div class="task-header-info">
                <span class="task-name">{{ task.name }}</span>
                <span class="task-type-badge">{{ task.type }}</span>
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
          <button @click="submitCuration(group.journal_id)" class="submit-btn">Complete Curation</button>
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
const allTasks = ref([]);

const journalGroups = computed(() => {
  if (!allTasks.value.length) return [];
  
  const groups = allTasks.value.reduce((acc, journal) => {
    acc[journal.journal_id] = {
      journal_id: journal.journal_id,
      journal_date: journal.journal_date,
      total_tasks: journal.total_tasks,
      tasks: journal.entities,
    };
    return acc;
  }, {});
  
  return Object.values(groups);
});

onMounted(() => {
  // TODO: Replace with actual API call to fetch pending curations
  // For example:
  // fetch('/api/curation/pending/entities')
  //   .then(res => res.json())
  //   .then(data => {
  //     allTasks.value = data;
  //   })
  //   .catch(err => console.error("Failed to fetch curation tasks:", err))
  //   .finally(() => isLoading.value = false);

  // Using mock data for now
  setTimeout(() => {
    allTasks.value = mockPendingCurations;
    isLoading.value = false;
  }, 500);
});

function navigateToCuration(journalId) {
  // Assuming a route like '/curation/:journalId' and named 'CurationView'
  router.push({ name: 'CurationView', params: { journalId } });
}

function quickAccept(group, taskIndex) {
  const task = group.tasks[taskIndex];
  console.log('Quick Accept:', task.name, 'from journal', group.journal_id);
  // TODO: API call to accept the entity
  // On success, remove from list
  group.tasks.splice(taskIndex, 1);
}

function quickReject(group, taskIndex) {
  const task = group.tasks[taskIndex];
  console.log('Quick Reject:', task.name, 'from journal', group.journal_id);
  // TODO: API call to reject the entity
  // On success, remove from list
  group.tasks.splice(taskIndex, 1);
}

function submitCuration(journalId) {
  console.log('Submitting curation for journal', journalId);
  // TODO: API call to submit/complete curation
  const groupIndex = allTasks.value.findIndex(g => g.journal_id === journalId);
  if (groupIndex > -1) {
    allTasks.value.splice(groupIndex, 1);
  }
}

// Mock Data
const mockPendingCurations = [
  {
    journal_id: "journal-abc-123",
    journal_date: "2025-09-15",
    total_tasks: 4,
    entities: [
      {
        "name": "Alice",
        "type": "PERSON",
        "summary_short": "Colleague involved in Minerva Project.",
        "summary": "Alice is a key stakeholder in the Minerva Project. We had a meeting today to discuss Q4 targets.",
        "occupation": "Project Manager",
        "birth_date": "1990-05-15"
      },
      {
        "name": "Minerva Project",
        "type": "PROJECT",
        "summary_short": "A project discussed with Alice.",
        "summary": "A project with Q4 targets. Progress seems to be on track.",
        "status": "In Progress",
        "start_date": "2025-07-01T00:00:00",
        "target_completion": "2025-12-31T00:00:00",
        "progress": 45.0
      },
    ]
  },
  {
    journal_id: "journal-def-456",
    journal_date: "2025-09-14",
    total_tasks: 5,
    entities: [
      {
        "name": "Project Phoenix Kickoff",
        "type": "EVENT",
        "summary_short": "Kickoff meeting for Project Phoenix.",
        "summary": "Attended the kickoff meeting for the new 'Project Phoenix'. It was a long but informative session.",
        "category": "Meeting",
        "date": "2025-09-15T14:00:00",
        "duration": "PT2H", // ISO 8601 duration format for 2 hours
        "location": "Conference Room 4B"
      },
      {
          "name": "Optimism",
          "type": "EMOTION",
          "summary_short": "Feeling optimistic about progress.",
          "summary": "A feeling of optimism regarding the current project progress after today's meetings.",
      },
      {
        "name": "Mate",
        "type": "CONSUMABLE",
        "summary_short": "A traditional South American caffeine-rich infused drink.",
        "summary": "Drank mate in the morning while reading news.",
        "category": "beverage"
      }
    ]
  }
];
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
