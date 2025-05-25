import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue')
    },
    {
      path: '/voice-chat',
      name: 'voice-chat',
      component: () => import('../views/VoiceChatView.vue')
    },
    {
      path: '/simple-voice-chat',
      name: 'simple-voice-chat',
      component: () => import('../views/SimpleVoiceChatView.vue')
    },
    {
      path: '/style-showcase',
      name: 'style-showcase',
      component: () => import('../views/StyleShowcaseView.vue')
    }
  ]
})

export default router 