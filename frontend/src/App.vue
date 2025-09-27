<template>
    <MinervaHeader />
    <div class="app-container">
        <router-view v-slot="{ Component }">
            <transition name="fade">
                <component :is="Component" />
            </transition>
        </router-view>
    </div>
</template>

<script setup>
import MinervaHeader from '@/components/curation/MinervaHeader.vue';
</script>

<style scoped>
.app-container {
  background-color: #4c4f52;
  background-image: url('@/assets/relief.png');
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  height: 100vh;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .5s;
}
.fade-enter, .fade-leave-to /* .fade-leave-active below version 2.1.8 */ {
  opacity: 0;
}
</style>