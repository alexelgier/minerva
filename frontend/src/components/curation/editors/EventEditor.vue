<template>
  <div class="entity-editor-container">
    <div class="editor-header">
      <h2>Edit Event</h2>
      <span class="entity-type-badge">Event</span>
    </div>
    <form @submit.prevent="onAccept" class="editor-form">
      <div class="form-group">
        <label for="name">Name</label>
        <input id="name" type="text" v-model="editableEntity.name" />
      </div>

      <div class="form-group">
        <label for="category">Category</label>
        <input id="category" type="text" v-model="editableEntity.category" />
      </div>

      <div class="form-group">
        <label for="date">Date</label>
        <input id="date" type="datetime-local" v-model="editableEntity.date" />
      </div>

      <div class="form-group">
        <label for="location">Location</label>
        <input id="location" type="text" v-model="editableEntity.location" />
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

watch(() => props.entity, (newEntity) => {
  editableEntity.value = JSON.parse(JSON.stringify(newEntity));
}, { immediate: true, deep: true });

const onAccept = () => {
  emit('accept', editableEntity.value);
};

const onReject = () => {
  emit('reject');
};
</script>
