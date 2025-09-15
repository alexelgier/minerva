<template>
  <div class="entity-editor-container">
    <div class="editor-header">
      <h2>Edit Person</h2>
      <span class="entity-type-badge">Person</span>
    </div>
    <form @submit.prevent="onAccept" class="editor-form">
      <div class="form-group">
        <label for="name">Name</label>
        <input id="name" type="text" v-model="editableEntity.name" />
      </div>

      <div class="form-group">
        <label for="occupation">Occupation</label>
        <input id="occupation" type="text" v-model="editableEntity.occupation" />
      </div>
      
      <div class="form-group">
        <label for="birth_date">Birth Date</label>
        <input id="birth_date" type="date" v-model="editableEntity.birth_date" />
      </div>

      <div class="form-group">
        <label for="summary_short">Short Summary</label>
        <input id="summary_short" type="text" v-model="editableEntity.summary_short" />
      </div>

      <div class="form-group">
        <label for="summary">Full Summary</label>
        <textarea id="summary" rows="4" v-model="editableEntity.summary"></textarea>
      </div>

      <div class="form-actions">
        <button type="button" @click="onReject" class="btn btn-reject">Reject</button>
        <button type="submit" class="btn btn-accept">Accept</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import './editor-styles.css';

const props = defineProps({
  entity: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['accept', 'reject']);

const editableEntity = ref({});

// When the entity prop changes, reset the local editable copy
watch(() => props.entity, (newEntity) => {
  // Create a deep copy to avoid mutating the prop directly
  editableEntity.value = JSON.parse(JSON.stringify(newEntity));
}, { immediate: true, deep: true });

const onAccept = () => {
  emit('accept', editableEntity.value);
};

const onReject = () => {
  emit('reject');
};
</script>
