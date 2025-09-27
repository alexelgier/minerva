<template>
<header class="curation-page-header">
      <button @click="goBackToQueue" class="back-btn" v-if="!isBackButtonDisabled">&larr; Back to Queue</button>
      <div class="spacer" v-else></div>
      <img src="@/assets/MinervaLogo.png" alt="Minerva Logo" height="49" style=""/>
</header>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

function goBackToQueue() {
  router.push('/curation-queue');
}
const isBackButtonDisabled = computed(() => {
  return router.currentRoute.value.name === 'CurationQueueView';
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

</style>