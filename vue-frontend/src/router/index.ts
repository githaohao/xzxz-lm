import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { checkLogin } from '@/utils/api'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false, hideForAuth: true }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/voice-chat',
      name: 'voice-chat',
      component: () => import('../views/VoiceChatView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/simple-voice-chat',
      name: 'simple-voice-chat',
      component: () => import('../views/SimpleVoiceChatView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/knowledge-base',
      name: 'knowledge-base',
      component: () => import('../views/KnowledgeBaseView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/components',
      name: 'components',
      component: () => import('../views/ComponentShowcaseView.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = checkLogin()
  
  // 如果目标路由需要认证
  if (to.meta.requiresAuth && !isLoggedIn) {
    // 未登录，重定向到登录页面，并保存原始路径
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }
  
  // 如果已登录且访问登录页面，重定向到首页
  if (to.meta.hideForAuth && isLoggedIn) {
    next('/')
    return
  }
  
  next()
})

export default router