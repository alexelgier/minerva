<template>
<header class="curation-page-header">
      <button @click="goBackToQueue" class="back-btn">&larr; Back to Queue</button>
      <img src="@/assets/MinervaLogo.png" alt="Minerva Logo" height="49"/>
</header>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

function goBackToQueue() {
  
}


</script>

<style scoped>

.curation-page-header {
  padding: 0.75rem 1.5rem;
  background-color: #1e2939;
  border-bottom: 1px solid #4a5565;
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