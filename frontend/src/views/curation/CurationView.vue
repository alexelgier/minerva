<template>
  <div>
    <header class="curation-page-header">
      <button @click="goBackToQueue" class="back-btn">&larr; Back to Queue</button>
    </header>
    <div v-if="isLoading" class="loading-message">Loading...</div>
    <div v-else class="curation-view">
      <div class="journal-panel">
        <JournalViewer :spans="entityToEdit?.data.spans" :markdown="markdown" />
      </div>
      <div class="editor-panel" v-if="entityToEdit">
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

function goBackToQueue() {
  router.push({ name: 'CurationQueueView' });
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
  filter: brightness(0.95);
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
  filter: brightness(0.95);
}

.curation-page-header {
  padding: 0.75rem 1.5rem;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.back-btn {
  font-size: 0.9rem;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  border: 1px solid #ced4da;
  background-color: #f8f9fa;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.back-btn:hover {
  background-color: #e9ecef;
}

.curation-view {
  display: flex;
  height: calc(100vh - 62px);
  width: 100%;
  background-color: #f0f2f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow-y: hidden;
}

.journal-panel {
  flex: 1;
  padding: 2rem;
  border-right: 1px solid #dcdfe6;
  overflow-y: auto;
  background-color: #ffffff;
}

.editor-panel {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.entity-type-heading {
  font-size: 1.3rem;
  font-weight: 600;
  color: #007bff;
  margin-bottom: 1.2rem;
  letter-spacing: 0.5px;
}

/* Responsive layout for smaller screens */
@media (max-width: 768px) {
  .curation-view {
    flex-direction: column;
    height: auto;
  }

  .journal-panel {
    border-right: none;
    border-bottom: 1px solid #dcdfe6;
    max-height: 50vh;
  }

  .editor-panel {
    max-height: 50vh;
  }
}
</style>
