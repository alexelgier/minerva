<template>
<header class="curation-page-header">
      <nav class="nav-links">
        <router-link to="/curation-queue" class="nav-link">Queue</router-link>
        <router-link to="/quotes" class="nav-link">Quotes</router-link>
        <router-link to="/concepts" class="nav-link">Concepts</router-link>
        <router-link to="/inbox" class="nav-link">Inbox</router-link>
        <router-link to="/notifications" class="nav-link">
          Notifications
          <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
        </router-link>
      </nav>
      <img src="@/assets/MinervaLogo.png" alt="Minerva Logo" height="49" style=""/>
</header>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const unreadCount = ref(0);
const API = import.meta.env.VITE_API_BASE_URL || '/api/curation';

onMounted(async () => {
  try {
    const r = await fetch(`${API}/notifications?unread_only=true&limit=0`);
    if (r.ok) {
      const data = await r.json();
      unreadCount.value = data.total ?? (data.notifications?.length ?? 0);
    }
  } catch (_) {
    // ignore
  }
});
</script>

<style scoped>

.curation-page-header {
  padding: 0.75rem 2rem;
  background-color: #222325;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: space-between;
}


.back-btn {
  font-size: 0.9rem;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  border: 1px solid #4a5565;
  background-color: #1e2939;
  color: #9eb0c2;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.back-btn:hover {
  background-color: #4a5565;
  color: white;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-link {
  color: #9eb0c2;
  text-decoration: none;
  font-size: 0.9rem;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  position: relative;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: white;
  background-color: rgba(74, 85, 101, 0.5);
}

.unread-badge {
  background: #dc3545;
  color: white;
  font-size: 0.75rem;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  margin-left: 0.25rem;
}

</style>