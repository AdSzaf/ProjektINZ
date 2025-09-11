import { createRouter, createWebHistory } from 'vue-router'
import MainView from '../components/MainView.vue'
import DashboardView from '../components/DashboardView.vue'
import HomeView from '../components/HomeView.vue'
import LoginView from '../components/LoginView.vue'
import RegistrationView from '../components/RegistrationView.vue'
import BoardView from '../components/BoardView.vue'
import BacklogView from '../components/BacklogView.vue'
import IssueView from '../components/IssuesView.vue'
import ReportsView from '../components/ReportsView.vue'
import MembersView from '../components/MembersView.vue'
import SettingsView from '../components/SettingsView.vue'
import CreateProjectView from '../components/CreateProjectView.vue'
import EpicsView from '../components/EpicsView.vue'
import SprintsView from '../components/SprintsView.vue'
import SuccessRedirect from '../components/SuccessRedirect.vue'
import CancelRedirect from '../components/CancelRedirect.vue'

const routes = [
  {
    path: '/',
    component: MainView,
    children: [
      { path: '/', redirect: '/login' },
      { path: 'dashboard', component: DashboardView },
      { path: 'home', component: HomeView },
      { path: 'board', component: BoardView },
      { path: 'backlog', component: BacklogView },
      { path: 'issues', component: IssueView },
      { path: 'reports', component: ReportsView },
      { path: 'members', component: MembersView },
      { path: 'settings', component: SettingsView },
      { path: 'create-project', component: CreateProjectView },
      { path: 'epics', component: EpicsView },
      { path: 'sprints', component: SprintsView, alias: '/Sprints' },
      { path: '/success', component: SuccessRedirect },
      { path: '/cancel', component: CancelRedirect }
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