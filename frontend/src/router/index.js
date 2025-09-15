import { createRouter, createWebHistory } from 'vue-router'
import CurationQueueView from '../views/curation/CurationQueueView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
      // TODO: Create a dedicated component for single journal curation
      component: () => import('../views/curation/CurationQueueView.vue')
    }
  ]
})

export default router
