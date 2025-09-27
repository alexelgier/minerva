<template>
  <div>
    <div v-if="isLoading" class="loading-message">Loading...</div>
    <div v-else class="curation-container">
      <!-- Navigation Bar -->
      <div class="navigation-bar">
        <button 
          class="nav-arrow nav-arrow-left" 
          @click="navigateToPrevious"
          :disabled="!previousJournalId"
          :class="{ disabled: !previousJournalId }"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-text">Previous Entry</span>
        </button>
        <button 
          class="nav-arrow nav-arrow-right" 
          @click="navigateToNext"
          :disabled="!nextJournalId"
          :class="{ disabled: !nextJournalId }"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-text">Next Entry</span>
        </button>
      </div>

      <div class="curation-view">
        <div class="journal-panel">
          <JournalViewer :spans="entityToEdit?.data.spans" :markdown="markdown" />
        </div>
        <div class="editor-panel" v-if="entityToEdit">
          <div class="editor-panel-well">
            <div class="editor-header-row">
              <h3 class="entity-type-heading">Entity Type: {{ entityToEdit.data.type }}</h3>
              <div class="editor-actions">
                <button class="accept-btn" @click="handleAccept">Accept</button>
                <button class="reject-btn" @click="handleReject">Reject</button>
              </div>
            </div>
            <div class="entity-fields-form">
              <component v-for="(inputType, field) in currentEntityFields" :key="field" :is="inputComponent(inputType)"
                v-model="fieldRefs[field]" :label="field" :placeholder="field" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import JournalViewer from '@/components/curation/JournalViewer.vue';
import { entityTypeFields } from '@/entityTypeFields.js';
import { useCurationStore } from '@/stores/curation';

const router = useRouter();
const route = useRoute();
const journalId = computed(() => route.params.journalId);
const entityId = computed(() => route.params.entityId);

const curation = useCurationStore();
onMounted(() => {
  curation.fetchCurationQueue();

});
const markdown = computed(() => curation.journalEntries[journalId.value]?.entry_text || '');

const entityToEdit = computed(() => curation.journalEntries[journalId.value]?.tasks[entityId.value]);
const isLoading = computed(() => curation.isLoading);

// Navigation computed properties
const previousJournalId = computed(() => curation.getPreviousJournalId(journalId.value));
const nextJournalId = computed(() => curation.getNextJournalId(journalId.value));

// Navigation methods
function navigateToPrevious() {
  if (previousJournalId.value) {
    // Get the first entity from the previous journal
    const prevJournal = curation.journalEntries[previousJournalId.value];
    const firstEntityId = Object.keys(prevJournal.tasks)[0];
    router.push(`/curation/${previousJournalId.value}/${firstEntityId}`);
  }
}

function navigateToNext() {
  if (nextJournalId.value) {
    // Get the first entity from the next journal
    const nextJournal = curation.journalEntries[nextJournalId.value];
    const firstEntityId = Object.keys(nextJournal.tasks)[0];
    router.push(`/curation/${nextJournalId.value}/${firstEntityId}`);
  }
}



// Build a map of computed refs, one per field
function makeFieldRefs(fields) {
  const result = {};
  for (const field in fields) {
    result[field] = computed({
      get: () => entityToEdit.value.data[field],
      set: (val) => curation.editedEntity[field].set(val),
    });
  }
  return result;
}

const currentEntityFields = computed(() => {
  const type = entityToEdit.value.data.type;
  return entityTypeFields[type] || {};
});
const editedEntity = computed(() => curation.editedEntity);
const fieldRefs = computed(() => makeFieldRefs(currentEntityFields.value));

function inputComponent(type) {
  switch (type) {
    case 'Input':
      return defineAsyncComponent(() => import('@/components/curation/inputs/StringInput.vue'));
    case 'TextAreaInput':
      return defineAsyncComponent(() => import('@/components/curation/inputs/TextAreaInput.vue'));
    case 'DateInput':
      return defineAsyncComponent(() => import('@/components/curation/inputs/DateInput.vue'));
    case 'DateTimeInput':
      return defineAsyncComponent(() => import('@/components/curation/inputs/DateTimeInput.vue'));
    case 'SliderInput':
      return defineAsyncComponent(() => import('@/components/curation/inputs/SliderInput.vue'));
    case 'DurationInput':
      return defineAsyncComponent(() => import('@/components/curation/inputs/DurationInput.vue'));
    case 'SpansInput':
      return defineAsyncComponent(() => import('@/components/curation/inputs/SpansInput.vue'));
    default:
      return defineAsyncComponent(() => import('@/components/curation/inputs/StringInput.vue'));
  }
}

function handleAccept() {
  console.log('Accepted:', editedEntity.value);
  // Here you would typically send the data to an API
  // and then load the next entity.
}

function handleReject() {
  console.log('Rejected:', entityToEdit.value.name);
  // Here you would typically flag this entity and load the next one.
}
</script>

<style scoped>
.editor-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.editor-actions {
  display: flex;
  gap: 1rem;
}

.accept-btn {
  font-size: 1rem;
  padding: 0.5rem 1.5rem;
  border-radius: 999px;
  border: none;
  background-color: #28a745;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.accept-btn.edited {
  background-color: #007bff;
}

.accept-btn:hover {
  background-color: #218838;
}

.reject-btn {
  font-size: 1rem;
  padding: 0.5rem 1.5rem;
  border-radius: 999px;
  border: none;
  background-color: #dc3545;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.reject-btn:hover {
  background-color: #c82333;
}

.curation-view {
  display: flex;
  height: calc(100vh - 59px - 60px); /* Full height minus header minus navigation bar */
  width: 100%;
  
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow-y: hidden;
  color: rgb(211, 211, 211);
}

.journal-panel {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.editor-panel {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.editor-panel-well {
  padding: 1.2rem;
  background: rgba(69, 76, 82, 0.3);
  backdrop-filter: blur(4px);
  border-radius: 5px;
  box-shadow: 2px 4px 8px rgba(0, 0, 0, 0.5);
}

.entity-type-heading {
  font-size: 1.3rem;
  font-weight: 600;
  color: #9eb0c2;
  margin-bottom: 1.2rem;
  letter-spacing: 0.5px;
}

/* Container Styles */
.curation-container {
  height: calc(100vh - 59px); /* Full height minus header */
  width: 100%;
  background-color: transparent;

}

/* Navigation Bar Styles */
.navigation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 2rem;
  background-color: rgba(54, 52, 52, 0.3);
  backdrop-filter: blur(4px);
  border-bottom: 1px solid #1a1b1c;
}

.nav-arrow {
  background: #1a1b1c;
  border: 1px solid #3a3c3e;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #d3d3d3;
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-arrow:hover:not(.disabled) {
  background: #2a2c2e;
  border-color: #4a4c4e;
  transform: scale(1.05);
}

.nav-arrow.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: #0f1011;
  border-color: #2a2c2e;
  color: #6a6c6e;
}

.nav-arrow-left {
  margin-left: 1rem;
}

.nav-arrow-right {
  margin-right: 1rem;
}

.nav-text {
  white-space: nowrap;
}

/* Responsive layout for smaller screens */
@media (max-width: 768px) {
  .curation-view {
    flex-direction: column;
    height: auto;
  }

  .journal-panel {
    border-right: none;
    border-bottom: 1px solid #373f4b;
    max-height: 50vh;
  }

  .editor-panel {
    max-height: 50vh;
  }

  .nav-arrow {
    width: 50px;
    height: 50px;
  }

  .navigation-bar {
    padding: 0 1rem;
  }
}
</style>
