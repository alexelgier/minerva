import { createRouter, createWebHistory } from 'vue-router'
import CurationQueueView from '../views/curation/CurationQueueView.vue'
import CurationView from '../views/curation/CurationView.vue'
import QuoteCurationView from '../views/curation/QuoteCurationView.vue'
import ConceptCurationView from '../views/curation/ConceptCurationView.vue'
import InboxCurationView from '../views/curation/InboxCurationView.vue'
import NotificationsView from '../views/curation/NotificationsView.vue'

const router = createRouter({
  history: createWebHistory(),
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
      path: '/curation/:journalId/:entityId',
      name: 'CurationView',
      component: CurationView
    },
    {
      path: '/quotes',
      name: 'QuoteCurationView',
      component: QuoteCurationView
    },
    {
      path: '/concepts',
      name: 'ConceptCurationView',
      component: ConceptCurationView
    },
    {
      path: '/inbox',
      name: 'InboxCurationView',
      component: InboxCurationView
    },
    {
      path: '/notifications',
      name: 'NotificationsView',
      component: NotificationsView
    }
  ]
})

export default router
