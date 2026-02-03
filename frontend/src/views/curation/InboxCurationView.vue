<template>
  <div class="inbox-curation-view">
    <header class="queue-header">
      <h1>Inbox Classification Curation</h1>
      <p v-if="isLoading">Loading...</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </header>
    <div v-if="!isLoading && !error">
      <div v-if="!workflowId" class="workflow-list">
        <p v-if="workflowIds.length === 0">No pending inbox classification workflows.</p>
        <div
          v-for="id in workflowIds"
          :key="id"
          class="workflow-card"
          @click="selectWorkflow(id)"
        >
          <strong>Workflow {{ id }}</strong>
        </div>
      </div>
      <div v-else class="items-view">
        <button @click="workflowId = null" class="back-btn">← Back</button>
        <ul class="item-list">
          <li v-for="item in items" :key="item.uuid" class="item-row">
            <div class="item-content">
              <span class="status-badge" :class="item.status">{{ item.status }}</span>
              <strong>{{ (item.original_data_json || item).note_title || (item.original_data_json || item).source_path }}</strong>
              <p>→ {{ (item.original_data_json || item).target_folder }}</p>
              <p v-if="(item.original_data_json || item).reason" class="reason">{{ (item.original_data_json || item).reason }}</p>
            </div>
            <div v-if="item.status === 'PENDING'" class="item-actions">
              <button @click="handleAction(item.uuid, 'accept')" class="accept-btn">Accept</button>
              <button @click="handleAction(item.uuid, 'reject')" class="reject-btn">Reject</button>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const API = 'http://127.0.0.1:8000/api/curation'
const workflowIds = ref([])
const items = ref([])
const workflowId = ref(null)
const isLoading = ref(false)
const error = ref(null)

async function fetchWorkflowIds() {
  isLoading.value = true
  error.value = null
  try {
    const r = await fetch(`${API}/inbox/pending`)
    if (!r.ok) throw new Error(r.statusText)
    const data = await r.json()
    workflowIds.value = data.workflow_ids || []
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

async function fetchItems() {
  if (!workflowId.value) return
  isLoading.value = true
  error.value = null
  try {
    const r = await fetch(`${API}/inbox/${workflowId.value}/items`)
    if (!r.ok) throw new Error(r.statusText)
    const data = await r.json()
    items.value = data.items || []
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

function selectWorkflow(id) {
  workflowId.value = id
}

watch(workflowId, (id) => {
  if (id) fetchItems()
})

async function handleAction(itemId, action) {
  try {
    const r = await fetch(`${API}/inbox/${workflowId.value}/${itemId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, curated_data: action === 'accept' ? {} : null }),
    })
    if (!r.ok) throw new Error(r.statusText)
    await fetchItems()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(() => fetchWorkflowIds())
</script>

<style scoped>
.workflow-card { padding: 0.5rem 1rem; border: 1px solid #ccc; margin: 0.25rem 0; cursor: pointer; }
.item-row { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid #eee; }
.reason { font-size: 0.9rem; color: #666; }
.back-btn { margin: 0.5rem; padding: 0.25rem 0.5rem; }
.accept-btn { margin-right: 0.25rem; }
.error-message { color: red; }
</style>
