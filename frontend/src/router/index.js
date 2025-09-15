import { createRouter, createWebHistory } from 'vue-router'
import CurationQueueView from '../views/curation/CurationQueueView.vue'
import CurationView from '../views/curation/CurationView.vue'

const router = createRouter({
  history: createWebHistory(process.env.VUE_APP_BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/curation-queue'
    },
    {
      path: '/curation-queue',
      name: 'CurationQueueView',
      component: CurationQueueView
    },
    {
      path: '/curation/:journalId',
      name: 'CurationView',
      component: CurationView
    }
  ]
})

export default router
