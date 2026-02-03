<template>
  <div class="concept-curation-view">
    <header class="queue-header">
      <h1>Concept Curation</h1>
      <p v-if="isLoading">Loading...</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </header>
    <div v-if="!isLoading && !error">
      <div v-if="!workflowId" class="workflow-list">
        <p v-if="workflows.length === 0">No pending concept workflows.</p>
        <div
          v-for="w in workflows"
          :key="w.workflow_id"
          class="workflow-card"
          @click="selectWorkflow(w.workflow_id)"
        >
          <strong>Content: {{ w.content_uuid }}</strong>
          <span>{{ w.overall_status }}</span>
        </div>
      </div>
      <div v-else class="items-view">
        <button @click="workflowId = null" class="back-btn">← Back</button>
        <button @click="completeWorkflow" class="complete-btn">Complete workflow</button>
        <h3>Concepts</h3>
        <ul class="item-list">
          <li v-for="c in concepts" :key="c.uuid" class="item-row">
            <div class="item-content">
              <span class="status-badge" :class="c.status">{{ c.status }}</span>
              <strong>{{ (c.original_data_json || c).title }}</strong>
              <p>{{ (c.original_data_json || c).concept?.slice(0, 100) }}...</p>
            </div>
            <div v-if="c.status === 'PENDING'" class="item-actions">
              <button @click="handleConcept(c.uuid, 'accept')" class="accept-btn">Accept</button>
              <button @click="handleConcept(c.uuid, 'reject')" class="reject-btn">Reject</button>
            </div>
          </li>
        </ul>
        <h3>Relations</h3>
        <ul class="item-list">
          <li v-for="r in relations" :key="r.uuid" class="item-row">
            <div class="item-content">
              <span class="status-badge" :class="r.status">{{ r.status }}</span>
              <span>{{ (r.original_data_json || r).relation_type }} / {{ (r.original_data_json || r).source_id }} → {{ (r.original_data_json || r).target_id }}</span>
            </div>
            <div v-if="r.status === 'PENDING'" class="item-actions">
              <button @click="handleRelation(r.uuid, 'accept')" class="accept-btn">Accept</button>
              <button @click="handleRelation(r.uuid, 'reject')" class="reject-btn">Reject</button>
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
const concepts = ref([])
const relations = ref([])
const workflowId = ref(null)
const isLoading = ref(false)
const error = ref(null)

async function fetchWorkflows() {
  isLoading.value = true
  error.value = null
  try {
    const r = await fetch(`${API}/concepts/pending`)
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
    const r = await fetch(`${API}/concepts/${workflowId.value}/items`)
    if (!r.ok) throw new Error(r.statusText)
    const data = await r.json()
    concepts.value = data.concepts || []
    relations.value = data.relations || []
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

async function handleConcept(conceptId, action) {
  try {
    const r = await fetch(`${API}/concepts/${workflowId.value}/${conceptId}`, {
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

async function handleRelation(relationId, action) {
  try {
    const r = await fetch(`${API}/concepts/${workflowId.value}/relations/${relationId}`, {
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
    const r = await fetch(`${API}/concepts/${workflowId.value}/complete`, {
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
