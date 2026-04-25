import { createRouter, createWebHistory } from 'vue-router'
import Login from '../view/login.vue'
import Home from '../view/home.vue'

const routes = [
    { path: '/', redirect: '/login' },
    { path: '/login', component: Login },
    { path: '/home', component: Home }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router