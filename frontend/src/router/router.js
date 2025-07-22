import { createRouter, createWebHistory } from 'vue-router'
import MainView from '../components/MainView.vue'
import DashboardView from '../components/DashboardView.vue'
import HomeView from '../components/HomeView.vue'
import LoginView from '../components/LoginView.vue'
import RegistrationView from '../components/RegistrationView.vue'
// import other views as needed

const routes = [
  {
    path: '/',
    component: MainView,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: DashboardView },
      { path: 'home', component: HomeView },
      // Add more child routes for other sidebar options
      // { path: 'backlog', component: BacklogView },
      // { path: 'sprint', component: SprintView },
      // etc.
    ]
  },
  { path: '/login', component: LoginView },
  { path: '/register', component: RegistrationView }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router