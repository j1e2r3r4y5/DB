import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../view/login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../view/home.vue'),
    redirect: '/home/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../view/dashboard.vue'),
        meta: { title: '监控大屏' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('../components/device.vue'),
        meta: { title: '设备管理' }
      },
      {
        path: 'devices/add',
        name: 'DeviceAdd',
        component: () => import('../components/deviceadd.vue'),
        meta: { title: '新建设备' }
      },
      {
        path: 'devlist',
        name: 'DevList',
        component: () => import('../components/devlist.vue'),
        meta: { title: '设备列表' }
      },
      {
        path: 'variables/:devId?',
        name: 'Variables',
        component: () => import('../components/variables/variables.vue'),
        meta: { title: '变量管理' }
      },
      {
        path: 'variables/send-config',
        name: 'SendConfigPage',
        component: () => import('../components/variables/SendConfigPage.vue'),
        meta: { title: '下发配置' }
      },
      {
        path: 'variables/batch-delete',
        name: 'BatchDeletePage',
        component: () => import('../components/variables/BatchDeletePage.vue'),
        meta: { title: '批量删除' }
      },
      {
        path: 'data/:devId',
        name: 'Data',
        component: () => import('../components/data/data.vue'),
        meta: { title: '数据管理' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../components/Administrator.vue'),
        meta: { title: '用户管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
