<template>
  <div>
    <header class="curation-page-header">
      <button @click="goBackToQueue" class="back-btn">&larr; Back to Queue</button>
    </header>
    <div class="curation-view">
      <div class="journal-panel">
        <JournalViewer :markdown="journalMarkdown" />
      </div>
      <div class="editor-panel">
        <component
          :is="editorComponent"
          :entity="entityToEdit"
          @accept="handleAccept"
          @reject="handleReject"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import JournalViewer from '@/components/curation/JournalViewer.vue';
import PersonEditor from '@/components/curation/editors/PersonEditor.vue';
import EventEditor from '@/components/curation/editors/EventEditor.vue';
import ProjectEditor from '@/components/curation/editors/ProjectEditor.vue';
import GenericEntityEditor from '@/components/curation/editors/GenericEntityEditor.vue';

const router = useRouter();

// Mock Data
const journalMarkdown = ref(`
# Journal Entry - 2025-09-15

Had a productive meeting with **Alice** about the *Minerva Project*. She seems confident we can hit the Q4 target.
Later, I attended the project kickoff for 'Project Phoenix'. It was a long meeting.
I'm feeling optimistic about our progress.
`);

const mockEntities = [
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
  }
];

const currentEntityIndex = ref(0);
const entityToEdit = computed(() => mockEntities[currentEntityIndex.value]);

const editorMap = {
  PERSON: PersonEditor,
  EVENT: EventEditor,
  PROJECT: ProjectEditor,
  // Add other entity types here
};

const editorComponent = computed(() => {
  return editorMap[entityToEdit.value.type] || GenericEntityEditor;
});

function goBackToQueue() {
  router.push({ name: 'CurationQueueView' });
}

function handleAccept(updatedEntity) {
  console.log('Accepted:', updatedEntity);
  // Here you would typically send the data to an API
  // and then load the next entity.
  goToNextEntity();
}

function handleReject() {
  console.log('Rejected:', entityToEdit.value.name);
  // Here you would typically flag this entity and load the next one.
  goToNextEntity();
}

function goToNextEntity() {
    currentEntityIndex.value = (currentEntityIndex.value + 1) % mockEntities.length;
}
</script>

<style scoped>
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
