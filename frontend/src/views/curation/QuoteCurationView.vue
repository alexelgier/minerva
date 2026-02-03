<template>
  <div class="quote-curation-view">
    <header class="queue-header">
      <h1>Quote Curation</h1>
      <p v-if="isLoading">Loading...</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </header>
    <div v-if="!isLoading && !error">
      <div v-if="!workflowId" class="workflow-list">
        <p v-if="workflows.length === 0">No pending quote workflows.</p>
        <div
          v-for="w in workflows"
          :key="w.workflow_id"
          class="workflow-card"
          @click="selectWorkflow(w.workflow_id)"
        >
          <strong>{{ w.content_title || w.file_path }}</strong>
          <span>{{ w.content_author }}</span>
        </div>
      </div>
      <div v-else class="items-view">
        <button @click="workflowId = null" class="back-btn">← Back</button>
        <button @click="completeWorkflow" class="complete-btn">Complete workflow</button>
        <ul class="item-list">
          <li v-for="item in items" :key="item.uuid" class="item-row">
            <div class="item-content">
              <span class="status-badge" :class="item.status">{{ item.status }}</span>
              <p>{{ (item.original_data_json || item).text?.slice(0, 120) }}...</p>
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
const workflows = ref([])
const items = ref([])
const workflowId = ref(null)
const isLoading = ref(false)
const error = ref(null)

async function fetchWorkflows() {
  isLoading.value = true
  error.value = null
  try {
    const r = await fetch(`${API}/quotes/pending`)
    if (!r.ok) throw new Error(r.statusText)
    const data = await r.json()
    workflows.value = data.workflows || []
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
    const r = await fetch(`${API}/quotes/${workflowId.value}/items`)
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

async function handleAction(quoteId, action) {
  try {
    const r = await fetch(`${API}/quotes/${workflowId.value}/${quoteId}`, {
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

async function completeWorkflow() {
  try {
    const r = await fetch(`${API}/quotes/${workflowId.value}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!r.ok) throw new Error(r.statusText)
    workflowId.value = null
    await fetchWorkflows()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(() => fetchWorkflows())
</script>

<style scoped>
.workflow-card { padding: 0.5rem 1rem; border: 1px solid #ccc; margin: 0.25rem 0; cursor: pointer; }
.item-row { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid #eee; }
.back-btn, .complete-btn { margin: 0.5rem; padding: 0.25rem 0.5rem; }
.accept-btn { margin-right: 0.25rem; }
.error-message { color: red; }
</style>
