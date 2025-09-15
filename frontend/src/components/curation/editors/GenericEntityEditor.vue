<template>
  <div class="entity-editor-container">
    <div class="editor-header">
      <h2>Edit {{ entity.type }}</h2>
      <span class="entity-type-badge">{{ entity.type }}</span>
    </div>
    <p>This entity type (<strong>{{ entity.type }}</strong>) does not have a dedicated editor yet.</p>
    <form @submit.prevent="onAccept" class="editor-form">
      <div class="form-group">
        <label for="name">Name</label>
        <input id="name" type="text" v-model="editableEntity.name" />
      </div>

      <div class="form-group">
        <label for="summary_short">Short Summary</label>
        <input id="summary_short" type="text" v-model="editableEntity.summary_short" />
      </div>

      <div class="form-group">
        <label for="summary">Full Summary</label>
        <textarea id="summary" rows="4" v-model="editableEntity.summary"></textarea>
      </div>
      
      <div class="form-group">
          <label>Other Properties</label>
          <pre class="raw-json">{{ otherProperties }}</pre>
          <p class="json-notice">Other properties are not editable in this generic view.</p>
      </div>

      <div class="form-actions">
        <button type="button" @click="onReject" class="btn btn-reject">Reject</button>
        <button type="submit" class="btn btn-accept">Accept</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import './editor-styles.css';

const props = defineProps({
  entity: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['accept', 'reject']);

const editableEntity = ref({});

// Separate standard fields from other properties
const otherProperties = computed(() => {
    const entityCopy = { ...props.entity };
    delete entityCopy.name;
    delete entityCopy.summary_short;
    delete entityCopy.summary;
    delete entityCopy.type;
    return JSON.stringify(entityCopy, null, 2);
});

watch(() => props.entity, (newEntity) => {
  editableEntity.value = JSON.parse(JSON.stringify(newEntity));
}, { immediate: true, deep: true });

const onAccept = () => {
  // Only emit the fields that were editable
  const updatedEntity = {
      ...props.entity, // keep non-editable fields
      name: editableEntity.value.name,
      summary_short: editableEntity.value.summary_short,
      summary: editableEntity.value.summary,
  };
  emit('accept', updatedEntity);
};

const onReject = () => {
  emit('reject');
};
</script>

<style scoped>
.raw-json {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    white-space: pre-wrap;
    word-break: break-all;
    font-size: 0.85em;
    max-height: 200px;
    overflow-y: auto;
}
.json-notice {
    font-size: 0.8em;
    color: #6c757d;
    margin-top: 5px;
}
</style>
