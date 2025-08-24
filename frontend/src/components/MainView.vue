<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useProjectStore } from '../stores/projectStore'

const router = useRouter()
const projectStore = useProjectStore()
const projects = computed(() => projectStore.projects)
const selectedProject = computed(() => projectStore.selectedProject)

// User and project data
const currentUser = ref({
  name: '',
  email: '',
  avatar: '',
  role: ''
})

const fetchCurrentUser = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
    }
    const res = await axios.get('/api/me/')
    currentUser.value = {
      name: `${res.data.first_name} ${res.data.last_name}`,
      email: res.data.email,
      avatar: (res.data.first_name[0] || '') + (res.data.last_name[0] || ''),
      role: res.data.role
    }
  } catch (e) {
    // Token invalid/expired, force logout
    localStorage.removeItem('token')
    router.push('/login')
  }
}

const fetchProjects = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  try {
    const res = await axios.get('/api/projects/')
    console.log('Fetched projects:', res.data)
    projects.value = res.data
    if (!projectStore.selectedProject && projects.value.length > 0) {
      projectStore.setProject(projects.value[0])
      localStorage.setItem('selectedProjectId', projects.value[0].id)
    }
    const lastId = localStorage.getItem('selectedProjectId')
    if (lastId) {
      const found = projects.value.find(p => p.id === lastId)
      if (found) projectStore.setProject(found)
    }
  } catch (e) {
    // handle error
  }
}

// UI state
const showUserDropdown = ref(false)
const showProjectDropdown = ref(false)
const showCreateDropdown = ref(false)
const searchQuery = ref('')
const notifications = ref(3)

// Dashboard data
const dashboardData = ref({
  activeSprintName: 'Sprint 23',
  sprintProgress: 65,
  openIssues: 24,
  inProgress: 8,
  completed: 42,
  velocity: 32,
  recentActivity: [
    { user: 'Alice Johnson', action: 'completed', item: 'AP-145: Login validation', time: '2 hours ago' },
    { user: 'Bob Smith', action: 'created', item: 'AP-146: Dashboard refactor', time: '4 hours ago' },
    { user: 'Charlie Brown', action: 'commented on', item: 'AP-143: User management', time: '6 hours ago' }
  ]
})

// Menu items
const menuItems = ref([
  { name: 'Home', icon: '🏠', route: '/home', active: false },
  { name: 'Dashboard', icon: '📊', route: '/dashboard', active: true },
  { name: 'Backlog', icon: '📋', route: '/backlog' },
  { name: 'Active Sprint', icon: '🏃', route: '/board' },
  { name: 'Epics', icon: '📚', route: '/epics' },
  { name: 'Sprints', icon: '🔄', route: '/sprints' },
  { name: 'Issues', icon: '🎯', route: '/issues' },
  { name: 'Reports', icon: '📈', route: '/reports' },
  { name: 'Team Members', icon: '👥', route: '/members' },
  { name: 'Settings', icon: '⚙️', route: '/settings' }
])

// Methods
const selectProject = (project) => {
  projectStore.setProject(project)
  showProjectDropdown.value = false
}
const toggleDropdown = (dropdown) => {
  showUserDropdown.value = dropdown === 'user' ? !showUserDropdown.value : false
  showProjectDropdown.value = dropdown === 'project' ? !showProjectDropdown.value : false
  showCreateDropdown.value = dropdown === 'create' ? !showCreateDropdown.value : false
}

const createNew = (type) => {
  console.log('Creating new:', type)
  showCreateDropdown.value = false
  // Handle creation logic here
}

const logout = () => {
  localStorage.removeItem('token');
  router.push('/login')
}

const searchIssues = () => {
  if (searchQuery.value.trim()) {
    console.log('Searching for:', searchQuery.value)
    // Handle search logic
  }
}

// Close dropdowns when clicking outside
const closeDropdowns = () => {
  showUserDropdown.value = false
  showProjectDropdown.value = false
  showCreateDropdown.value = false
}

onMounted(() => {
  document.addEventListener('click', closeDropdowns)
  fetchCurrentUser()
  projectStore.fetchProjects()
})
</script>

<template>
  <div class="dashboard-layout" @click="closeDropdowns">
    <!-- Top Navigation Bar -->
    <header class="top-nav">
      <div class="nav-left">
        <!-- Logo -->
        <div class="logo">
          <span class="logo-icon">🎯</span>
          <span class="logo-text">TaskFlow</span>
        </div>

        <!-- Project Selector -->
        <div class="project-selector" @click.stop>
          <button 
            class="project-btn" 
            @click="toggleDropdown('project')"
            :class="{ active: showProjectDropdown }"
          >
            <span class="project-key">{{ selectedProject?.key }}</span>
            <span class="project-name">{{ selectedProject?.name }}</span>
            <span class="dropdown-arrow">▼</span>
          </button>
          <div v-if="showProjectDropdown" class="dropdown project-dropdown">
            <div v-for="project in projects" :key="project.id" class="dropdown-item" @click="selectProject(project)">
                <span class="project-key">{{ project.key }}</span>
                <span class="project-name">{{ project.name }}</span>
            </div>
            <div v-if="projects.length === 0" style="padding:1rem;color:#888;">No projects found</div>
          </div>
        </div>

        <!-- Quick Create Button -->
        <div class="quick-create" @click.stop>
          <button class="create-btn" @click="router.push('/create-project')">
            + Create Project
          </button>
        </div>
      </div>

      <div class="nav-center">
        <!-- Search Bar -->
        <div class="search-bar">
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Search issues, epics, users..."
            @keyup.enter="searchIssues"
          />
          <button class="search-btn" @click="searchIssues">🔍</button>
        </div>
      </div>

      <div class="nav-right">
        <!-- Notifications -->
        <button class="notification-btn">
          🔔
          <span v-if="notifications > 0" class="notification-badge">{{ notifications }}</span>
        </button>

        <!-- User Menu -->
        <div class="user-menu" @click.stop>
          <button 
            class="user-btn"
            @click="toggleDropdown('user')"
            :class="{ active: showUserDropdown }"
          >
            <div class="user-avatar">{{ currentUser.avatar }}</div>
            <span class="dropdown-arrow">▼</span>
          </button>
          
          <div v-if="showUserDropdown" class="dropdown user-dropdown">
            <div class="user-info">
              <div class="user-name">{{ currentUser.name }}</div>
              <div class="user-email">{{ currentUser.email }}</div>
            </div>
            <hr>
            <div class="dropdown-item">👤 Profile</div>
            <div class="dropdown-item" @click="router.push('/settings')">⚙️ Settings</div>
            <hr>
            <div class="dropdown-item" @click="logout">🚪 Logout</div>
          </div>
        </div>
      </div>
    </header>

    <div class="main-layout">
      <!-- Sidebar -->
      <nav class="sidebar">
        <router-link 
          v-for="item in menuItems" 
          :key="item.name"
          :to="item.route"
          class="menu-item"
          :class="{ active: $route.path === item.route }"
        >
          <span class="menu-icon">{{ item.icon }}</span>
          <span class="menu-text">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- Main Content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: #f8f9fa;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

/* Top Navigation */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #e1e5e9;
  padding: 0 1rem;
  height: 60px;
  position: relative;
  z-index: 100;
  flex-shrink: 0;
  width: 100%;
}

.nav-left, .nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 400px;
  margin: 0 2rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: bold;
  color: #0066cc;
}

.logo-icon {
  font-size: 1.5rem;
}

.project-selector {
  position: relative;
}

.project-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.project-btn:hover, .project-btn.active {
  background: #e9ecef;
  border-color: #0066cc;
}

.project-key {
  background: #0066cc;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: bold;
}

.create-btn {
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-btn:hover, .create-btn.active {
  background: #0056b3;
}

.search-bar {
  display: flex;
  width: 100%;
  max-width: 400px;
}

.search-bar input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-right: none;
  border-radius: 4px 0 0 4px;
  outline: none;
}

.search-bar input:focus {
  border-color: #0066cc;
}

.search-btn {
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-left: none;
  border-radius: 0 4px 4px 0;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
}

.notification-btn {
  position: relative;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.notification-btn:hover {
  background: #f8f9fa;
}

.notification-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-btn:hover, .user-btn.active {
  background: #f8f9fa;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

/* Dropdowns */
.dropdown {
  position: absolute;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 200px;
}

.project-dropdown, .create-dropdown {
  top: 100%;
  left: 0;
  margin-top: 0.25rem;
}

.user-dropdown {
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
}

.dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dropdown-item:hover {
  background: #f8f9fa;
}

.user-info {
  padding: 0.75rem 1rem;
}

.user-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.9rem;
  color: #666;
}

/* Main Layout */
.main-layout {
  display: flex;
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 250px;
  background: white;
  border-right: 1px solid #e1e5e9;
  padding: 1rem 0;
  overflow-y: auto;
  flex-shrink: 0;
  height: 100%;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0 0.5rem;
  border-radius: 4px;
}

.menu-item:hover {
  background: #f8f9fa;
}

.menu-item.active {
  background: #e3f2fd;
  color: #0066cc;
  font-weight: 500;
}

.menu-icon {
  font-size: 1.1rem;
}

/* Main Content */
.main-content {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  padding: 2rem;
  overflow-y: auto;
  height: 100%;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.project-description {
  color: #666;
  margin: 0;
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.dashboard-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-card h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

/* Progress Bar */
.progress-container {
  margin-top: 1rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #28a745;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9rem;
  color: #666;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #0066cc;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
}

/* Activity Card */
.activity-card {
  grid-column: span 2;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.activity-content {
  flex: 1;
}

.activity-user {
  font-weight: 500;
  color: #0066cc;
}

.activity-action {
  margin: 0 0.25rem;
  color: #666;
}

.activity-item-name {
  font-weight: 500;
}

.activity-time {
  font-size: 0.9rem;
  color: #999;
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 768px) {
  .nav-center {
    display: none;
  }
  
  .sidebar {
    width: 200px;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .activity-card {
    grid-column: span 1;
  }
}

/* Dark Mode Styles */
@media (prefers-color-scheme: dark) {
  .dashboard-layout {
    background-color: #181a1b !important;
  }

  /* Top Navigation */
  .top-nav {
    background: #232526 !important;
    border-bottom: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .logo {
    color: #4ea1ff !important;
  }

  .logo-text {
    color: #f3f3f3 !important;
  }

  /* Project Selector */
  .project-btn {
    background: #181a1b !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .project-btn:hover, .project-btn.active {
    background: #232526 !important;
    border-color: #4ea1ff !important;
  }

  .project-key {
    background: #0056b3 !important;
    color: #fff !important;
  }

  .project-name {
    color: #f3f3f3 !important;
  }

  /* Create Button */
  .create-btn {
    background: #0056b3 !important;
    color: #fff !important;
  }

  .create-btn:hover, .create-btn.active {
    background: #004494 !important;
  }

  /* Search Bar */
  .search-bar input {
    background: #181a1b !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .search-bar input:focus {
    border-color: #4ea1ff !important;
  }

  .search-bar input::placeholder {
    color: #aaa !important;
  }

  .search-btn {
    background: #232526 !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .search-btn:hover {
    background: #333 !important;
  }

  /* Notification Button */
  .notification-btn {
    color: #f3f3f3 !important;
  }

  .notification-btn:hover {
    background: #232526 !important;
  }

  .notification-badge {
    background: #e74c3c !important;
    color: #fff !important;
  }

  /* User Menu */
  .user-btn {
    color: #f3f3f3 !important;
  }

  .user-btn:hover, .user-btn.active {
    background: #232526 !important;
  }

  .user-avatar {
    background: #0056b3 !important;
    color: #fff !important;
  }

  /* Dropdowns */
  .dropdown {
    background: #232526 !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .dropdown-item {
    color: #f3f3f3 !important;
  }

  .dropdown-item:hover {
    background: #181a1b !important;
  }

  .user-info .user-name {
    color: #f3f3f3 !important;
  }

  .user-info .user-email {
    color: #aaa !important;
  }

  /* Sidebar */
  .sidebar {
    background: #232526 !important;
    border-right: 1px solid #444 !important;
  }

  .menu-item {
    color: #f3f3f3 !important;
  }

  .menu-item:hover {
    background: #181a1b !important;
  }

  .menu-item.active {
    background: #1a3a52 !important;
    color: #4ea1ff !important;
  }

  /* Main Content */
  .main-content {
    background: #181a1b !important;
    color: #f3f3f3 !important;
  }

  /* Dashboard Cards */
  .dashboard-card {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .dashboard-card h3 {
    color: #f3f3f3 !important;
  }

  /* Progress Bar */
  .progress-bar {
    background: #333 !important;
  }

  .progress-fill {
    background: #28a745 !important;
  }

  .progress-text {
    color: #aaa !important;
  }

  /* Stats */
  .stat-number {
    color: #4ea1ff !important;
  }

  .stat-label {
    color: #aaa !important;
  }

  /* Activity Items */
  .activity-item {
    background: #181a1b !important;
    color: #f3f3f3 !important;
  }

  .activity-user {
    color: #4ea1ff !important;
  }

  .activity-action {
    color: #aaa !important;
  }

  .activity-item-name {
    color: #f3f3f3 !important;
  }

  .activity-time {
    color: #888 !important;
  }

  /* Dashboard Header */
  .dashboard-header h1 {
    color: #f3f3f3 !important;
  }

  .project-description {
    color: #aaa !important;
  }

  /* Dropdown Arrow */
  .dropdown-arrow {
    color: #f3f3f3 !important;
  }

  /* HR elements */
  hr {
    border-color: #444 !important;
  }
}
</style>