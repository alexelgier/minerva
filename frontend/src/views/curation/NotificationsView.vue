<template>
  <div class="notifications-view">
    <header class="queue-header">
      <h1>Notifications</h1>
      <p v-if="isLoading">Loading...</p>
      <p v-if="error" class="error-message">{{ error }}</p>
    </header>
    <div v-if="!isLoading && !error" class="notifications-list">
      <p v-if="notifications.length === 0">No notifications.</p>
      <div
        v-for="n in notifications"
        :key="n.id"
        class="notification-card"
        :class="{ unread: !n.read_at }"
      >
        <div class="notification-body">
          <strong>{{ n.title }}</strong>
          <p v-if="n.message" class="message">{{ n.message }}</p>
          <span class="meta">{{ n.workflow_type }} · {{ n.notification_type }} · {{ formatDate(n.created_at) }}</span>
        </div>
        <div class="notification-actions">
          <button v-if="!n.read_at" @click="markRead(n.id)" class="read-btn">Mark read</button>
          <button @click="markDismissed(n.id)" class="dismiss-btn">Dismiss</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/curation'
const notifications = ref([])
const total = ref(0)
const isLoading = ref(false)
const error = ref(null)

function formatDate(createdAt) {
  if (!createdAt) return ''
  const d = new Date(createdAt)
  return d.toLocaleString()
}

async function fetchNotifications() {
  isLoading.value = true
  error.value = null
  try {
    const r = await fetch(`${API}/notifications?limit=100`)
    if (!r.ok) throw new Error(r.statusText)
    const data = await r.json()
    notifications.value = data.notifications || []
    total.value = data.total ?? 0
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

async function markRead(id) {
  try {
    const r = await fetch(`${API}/notifications/${id}/read`, { method: 'POST' })
    if (!r.ok) throw new Error(r.statusText)
    await fetchNotifications()
  } catch (e) {
    error.value = e.message
  }
}

async function markDismissed(id) {
  try {
    const r = await fetch(`${API}/notifications/${id}/dismiss`, { method: 'POST' })
    if (!r.ok) throw new Error(r.statusText)
    await fetchNotifications()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(() => fetchNotifications())
</script>

<style scoped>
.notifications-view {
  padding: 2rem;
  background-color: transparent;
  min-height: calc(100vh - 59px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.queue-header h1 {
  color: #949999;
  margin-bottom: 1rem;
}
.error-message {
  color: #dc3545;
}
.notifications-list {
  max-width: 700px;
  margin: 0 auto;
}
.notification-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  margin-bottom: 0.5rem;
  background-color: rgba(69, 76, 82, 0.3);
  backdrop-filter: blur(5px);
  color: rgb(211, 211, 211);
  border-radius: 8px;
  border-left: 4px solid #4a5565;
}
.notification-card.unread {
  border-left-color: #9eb0c2;
}
.notification-body .message {
  margin: 0.5rem 0;
  font-size: 0.95rem;
  color: #b1c0cc;
}
.meta {
  font-size: 0.8rem;
  color: #888;
}
.notification-actions {
  display: flex;
  gap: 0.5rem;
}
.read-btn, .dismiss-btn {
  padding: 0.35rem 0.75rem;
  border-radius: 4px;
  border: 1px solid #4a5565;
  background: rgba(30, 41, 57, 0.8);
  color: #9eb0c2;
  cursor: pointer;
  font-size: 0.85rem;
}
.read-btn:hover, .dismiss-btn:hover {
  background: #4a5565;
  color: white;
}
</style>
