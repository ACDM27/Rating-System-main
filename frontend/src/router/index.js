import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
    {
        path: '/',
        redirect: '/login'
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue')
    },
    {
        path: '/admin/login',
        name: 'AdminLogin',
        component: () => import('../views/AdminLogin.vue')
    },
    {
        path: '/class-select',
        name: 'ClassSelect',
        component: () => import('../views/ClassSelect.vue'),
        meta: { requiresAuth: true }
    },
    // 管理员路由 - 辩论赛管理
    {
        path: '/admin',
        redirect: '/admin/debate'
    },
    {
        path: '/admin/students',
        name: 'AdminStudents',
        component: () => import('../views/admin/AudienceManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/admin/teachers',
        name: 'AdminTeachers',
        component: () => import('../views/admin/JudgeManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/admin/debaters',
        name: 'AdminDebaters',
        component: () => import('../views/admin/DebaterManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/admin/debate',
        name: 'AdminDebate',
        component: () => import('../views/admin/DebateDashboard.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    // 评委路由
    {
        path: '/judge',
        name: 'JudgeScoring',
        component: () => import('../views/judge/Scoring.vue'),
        meta: { requiresAuth: true, role: 'judge', requiresClass: true }
    },
    // 观众路由
    {
        path: '/audience',
        name: 'AudienceVoting',
        component: () => import('../views/audience/Voting.vue'),
        meta: { requiresAuth: true, role: 'audience', requiresClass: true }
    },
    // 大屏路由
    {
        path: '/screen',
        name: 'Screen',
        component: () => import('../views/screen/Display.vue')
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    // 检查登录
    if (to.meta.requiresAuth && !authStore.isLoggedIn) {
        next('/login')
        return
    }

    // 检查角色
    if (to.meta.role && authStore.user?.role !== to.meta.role) {
        const roleRoutes = {
            admin: '/admin',
            judge: '/judge',
            audience: '/audience'
        }
        next(roleRoutes[authStore.user?.role] || '/login')
        return
    }

    // 检查是否需要选择班级
    if (to.meta.requiresClass && !authStore.hasSelectedClass) {
        // 观众不需要手动选择班级
        if (authStore.user?.role === 'audience' && authStore.user?.class_id) {
            authStore.currentClassId = authStore.user.class_id
            next()
        } else {
            next('/class-select')
        }
        return
    }

    next()
})

export default router
