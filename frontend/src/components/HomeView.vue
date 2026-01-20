<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

const projectStore = useProjectStore()
const selectedProject = computed(() => projectStore.selectedProject)
const currentProject = computed(() => projectStore.selectedProject)

// Dashboard data
const dashboardData = ref({
  activeSprintName: 'No Active Sprint',
  sprintProgress: 0,
  openIssues: 0,
  inProgress: 0,
  completed: 0,
  velocity: 0,
  teamSize: 0,
  recentActivity: [],
  upcomingDeadlines: [],
  projectInfo: {}
})

// UI state
const loading = ref(false)
const error = ref(null)
const refreshInterval = ref(null)
const showCustomization = ref(false)

// Customization settings
const customizationSettings = ref({
  showSprintProgress: true,
  showQuickStats: true,
  showRecentActivity: true,
  showUpcomingDeadlines: true,
  refreshInterval: 30000, // 30 seconds
  theme: 'auto' // 'light', 'dark', 'auto'
})

// Load customization settings from localStorage
const loadCustomizationSettings = () => {
  const saved = localStorage.getItem('dashboardCustomization')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      customizationSettings.value = { ...customizationSettings.value, ...parsed }
    } catch (e) {
      console.warn('Failed to parse dashboard customization settings')
    }
  }
}

// Save customization settings to localStorage
const saveCustomizationSettings = () => {
  localStorage.setItem('dashboardCustomization', JSON.stringify(customizationSettings.value))
}

// Fetch dashboard data
const fetchDashboardData = async () => {
  if (!selectedProject.value?.id) {
    dashboardData.value = {
      activeSprintName: 'No Active Sprint',
      sprintProgress: 0,
      openIssues: 0,
      inProgress: 0,
      completed: 0,
      velocity: 0,
      teamSize: 0,
      recentActivity: [],
      upcomingDeadlines: [],
      projectInfo: {}
    }
    return
  }

  loading.value = true
  error.value = null

  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    const response = await axios.get(`/api/projects/${selectedProject.value.id}/dashboard/`)
    dashboardData.value = response.data
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false
  }
}

// Auto-refresh functionality
const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  
  if (customizationSettings.value.refreshInterval > 0) {
    refreshInterval.value = setInterval(() => {
      fetchDashboardData()
    }, customizationSettings.value.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// Customization methods
const toggleCard = (cardName) => {
  const settingKey = `show${cardName}`
  if (customizationSettings.value.hasOwnProperty(settingKey)) {
    customizationSettings.value[settingKey] = !customizationSettings.value[settingKey]
    saveCustomizationSettings()
  }
}

const updateRefreshInterval = (interval) => {
  customizationSettings.value.refreshInterval = interval
  saveCustomizationSettings()
  startAutoRefresh()
}

const updateTheme = (theme) => {
  customizationSettings.value.theme = theme
  saveCustomizationSettings()
  applyTheme(theme)
}

const applyTheme = (theme) => {
  if (theme === 'auto') {
    // Let CSS handle auto theme
    document.documentElement.removeAttribute('data-theme')
  } else {
    document.documentElement.setAttribute('data-theme', theme)
  }
}

// Manual refresh
const refreshData = () => {
  fetchDashboardData()
}

// Lifecycle
onMounted(() => {
  loadCustomizationSettings()
  fetchDashboardData()
  startAutoRefresh()
  applyTheme(customizationSettings.value.theme)
})

// Watch for project changes
watch(selectedProject, () => {
  fetchDashboardData()
}, { immediate: true })

// Cleanup on unmount
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="home-view">
    
    <div class="dashboard-header">
      <div class="header-content">
        <div>
          <h1>Project Dashboard</h1>
          <p class="project-description">
            <template v-if="selectedProject">
              {{ selectedProject.name }} - Overview and current sprint status
            </template>
            <template v-else>
              No projects yet. Create a project to get started!
            </template>
          </p>
        </div>
        <div class="header-controls">
          <button 
            class="refresh-btn" 
            @click="refreshData" 
            :disabled="loading"
            :class="{ 'loading': loading }"
          >
            <span v-if="loading">⟳</span>
            <span v-else>↻</span>
            Refresh
          </button>
          <button class="customize-btn" @click="showCustomization = !showCustomization">
            ⚙️ Customize
          </button>
        </div>
      </div>
    </div>

    
    <div v-if="showCustomization" class="customization-panel">
      <h3>Dashboard Customization</h3>
      <div class="customization-grid">
        <div class="customization-group">
          <h4>Visible Cards</h4>
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="customizationSettings.showSprintProgress"
              @change="saveCustomizationSettings"
            >
            Sprint Progress
          </label>
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="customizationSettings.showQuickStats"
              @change="saveCustomizationSettings"
            >
            Quick Stats
          </label>
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="customizationSettings.showRecentActivity"
              @change="saveCustomizationSettings"
            >
            Recent Activity
          </label>
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="customizationSettings.showUpcomingDeadlines"
              @change="saveCustomizationSettings"
            >
            Upcoming Deadlines
          </label>
        </div>
        <div class="customization-group">
          <h4>Auto-refresh</h4>
          <select 
            v-model="customizationSettings.refreshInterval" 
            @change="updateRefreshInterval(customizationSettings.refreshInterval)"
          >
            <option :value="0">Disabled</option>
            <option :value="10000">10 seconds</option>
            <option :value="30000">30 seconds</option>
            <option :value="60000">1 minute</option>
            <option :value="300000">5 minutes</option>
          </select>
        </div>
        <div class="customization-group">
          <h4>Theme</h4>
          <select 
            v-model="customizationSettings.theme" 
            @change="updateTheme(customizationSettings.theme)"
          >
            <option value="auto">Auto</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>
    </div>

    
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="refreshData" class="retry-btn">Retry</button>
    </div>

    
    <div v-if="selectedProject && !loading" class="dashboard-grid">
      
      <div v-if="customizationSettings.showSprintProgress" class="dashboard-card">
        <div class="card-header">
          <h3>{{ dashboardData.activeSprintName }} Progress</h3>
          <button class="card-toggle" @click="toggleCard('SprintProgress')">×</button>
        </div>
        <div class="progress-container">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: dashboardData.sprintProgress + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ dashboardData.sprintProgress }}% Complete</span>
        </div>
      </div>

      
      <div v-if="customizationSettings.showQuickStats" class="dashboard-card stats-card">
        <div class="card-header">
          <h3>Quick Stats</h3>
          <button class="card-toggle" @click="toggleCard('QuickStats')">×</button>
        </div>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ dashboardData.openIssues }}</div>
            <div class="stat-label">Open Issues</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ dashboardData.inProgress }}</div>
            <div class="stat-label">In Progress</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ dashboardData.completed }}</div>
            <div class="stat-label">Completed</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ dashboardData.velocity }}</div>
            <div class="stat-label">Velocity</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ dashboardData.teamSize }}</div>
            <div class="stat-label">Team Size</div>
          </div>
        </div>
      </div>

      
      <div v-if="customizationSettings.showRecentActivity" class="dashboard-card activity-card">
        <div class="card-header">
          <h3>Recent Activity</h3>
          <button class="card-toggle" @click="toggleCard('RecentActivity')">×</button>
        </div>
        <div class="activity-list">
          <div 
            v-for="activity in dashboardData.recentActivity" 
            :key="activity.time"
            class="activity-item"
          >
            <div class="activity-content">
              <span class="activity-user">{{ activity.user }}</span>
              <span class="activity-action">{{ activity.action }}</span>
              <span class="activity-item-name">{{ activity.item }}</span>
            </div>
            <div class="activity-time">{{ activity.time }}</div>
          </div>
          <div v-if="dashboardData.recentActivity.length === 0" class="no-activity">
            No recent activity
          </div>
        </div>
      </div>

      
      <div v-if="customizationSettings.showUpcomingDeadlines && dashboardData.upcomingDeadlines.length > 0" class="dashboard-card deadlines-card">
        <div class="card-header">
          <h3>Upcoming Deadlines</h3>
          <button class="card-toggle" @click="toggleCard('UpcomingDeadlines')">×</button>
        </div>
        <div class="deadlines-list">
          <div 
            v-for="deadline in dashboardData.upcomingDeadlines" 
            :key="deadline.key"
            class="deadline-item"
          >
            <div class="deadline-content">
              <span class="deadline-key">{{ deadline.key }}</span>
              <span class="deadline-title">{{ deadline.title }}</span>
              <span class="deadline-assignee">{{ deadline.assignee }}</span>
            </div>
            <div class="deadline-meta">
              <span class="deadline-priority" :class="'priority-' + deadline.priority">
                {{ deadline.priority }}
              </span>
              <span v-if="deadline.story_points" class="deadline-points">
                {{ deadline.story_points }} pts
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading dashboard data...</p>
    </div>

    
    <div v-if="!selectedProject && !loading" class="no-projects-message">
      <p>You have no projects yet.</p>
      <button class="create-btn" @click="$router.push('/create-project')">
        + Create Project
      </button>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  min-height: 100vh;
  background: #f8f9fa;
  padding-bottom: 3rem; 
}

.dashboard-header {
  margin-bottom: 2rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.dashboard-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.project-description {
  color: #666;
  margin: 0;
}

.header-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.refresh-btn, .customize-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.refresh-btn:hover, .customize-btn:hover {
  background: #f8f9fa;
  border-color: #0066cc;
}

.refresh-btn.loading {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn.loading span {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}


.customization-panel {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  border: 1px solid #e9ecef;
}

.customization-panel h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.customization-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.customization-group h4 {
  margin: 0 0 1rem 0;
  color: #555;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox-label input[type="checkbox"] {
  margin: 0;
}

.customization-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}


.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.retry-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}


.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

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
  transition: all 0.3s ease;
}

.dashboard-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.dashboard-card h3 {
  margin: 0;
  color: #333;
}

.card-toggle {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.card-toggle:hover {
  background: #f8f9fa;
  color: #666;
}

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
  transition: all 0.2s ease;
}

.activity-item:hover {
  background: #e9ecef;
  transform: translateX(4px);
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

.no-activity {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 2rem;
}


.deadlines-card {
  grid-column: span 2;
}

.deadlines-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.deadline-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.deadline-item:hover {
  background: #fff8e1;
  border-color: #ffd54f;
  transform: translateX(4px);
}

.deadline-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.deadline-key {
  font-weight: 600;
  color: #856404;
  font-size: 0.9rem;
}

.deadline-title {
  font-weight: 500;
  color: #333;
}

.deadline-assignee {
  font-size: 0.9rem;
  color: #666;
}

.deadline-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.deadline-priority {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.priority-highest {
  background: #f8d7da;
  color: #721c24;
}

.priority-high {
  background: #f5c6cb;
  color: #721c24;
}

.priority-medium {
  background: #fff3cd;
  color: #856404;
}

.priority-low {
  background: #d1ecf1;
  color: #0c5460;
}

.priority-lowest {
  background: #d4edda;
  color: #155724;
}

.deadline-points {
  font-size: 0.8rem;
  color: #666;
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.no-projects-message {
  text-align: center;
  margin-top: 3rem;
  color: #666;
}
.create-btn {
  margin-top: 1rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
}


@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .activity-card, .deadlines-card {
    grid-column: span 1;
  }
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  .header-controls {
    width: 100%;
    justify-content: flex-end;
  }
  .customization-grid {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .deadline-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  .deadline-meta {
    align-items: flex-start;
    flex-direction: row;
    gap: 0.5rem;
  }
}


@media (prefers-color-scheme: dark) {
  .home-view {
    background: #0d1117;
  }

  .dashboard-header, .customization-panel, .dashboard-card {
    background: #161b22 !important;
    border: 1px solid #30363d;
    box-shadow: 0 4px 8px rgba(1, 4, 9, 0.3) !important;
  }

  .dashboard-header h1, .customization-panel h3, .dashboard-card h3 {
    color: #f0f6fc !important;
  }

  .project-description, .customization-group h4 {
    color: #8b949e !important;
  }

  .refresh-btn, .customize-btn, .customization-group select {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .refresh-btn:hover, .customize-btn:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
  }

  .checkbox-label {
    color: #c9d1d9;
  }

  .error-message {
    background: #490202 !important;
    color: #f85149 !important;
  }

  .retry-btn {
    background: #da3633 !important;
  }

  .loading-state {
    color: #8b949e !important;
  }

  .activity-item, .deadline-item {
    background: #0d1117 !important;
    border-color: #21262d !important;
  }

  .activity-item:hover, .deadline-item:hover {
    background: #21262d !important;
    border-color: #30363d !important;
  }

  .activity-user {
    color: #58a6ff !important;
  }

  .activity-action, .deadline-assignee {
    color: #8b949e !important;
  }

  .activity-item-name, .deadline-title {
    color: #c9d1d9 !important;
  }

  .activity-time, .no-activity {
    color: #6e7681 !important;
  }

  .deadline-key {
    color: #f0a020 !important;
  }

  .stat-number {
    color: #58a6ff !important;
  }

  .stat-label {
    color: #8b949e !important;
  }

  .progress-bar {
    background: #21262d !important;
  }

  .progress-fill {
    background: #238636 !important;
  }

  .progress-text {
    color: #8b949e !important;
  }

  .no-projects-message {
    color: #8b949e !important;
  }

  .create-btn {
    background: #238636 !important;
    border-color: #238636 !important;
  }

  .create-btn:hover {
    background: #2ea043 !important;
    border-color: #2ea043 !important;
  }
}


[data-theme="dark"] {
  .home-view {
    background: #0d1117;
  }

  .dashboard-header, .customization-panel, .dashboard-card {
    background: #161b22 !important;
    border: 1px solid #30363d;
    box-shadow: 0 4px 8px rgba(1, 4, 9, 0.3) !important;
  }

  .dashboard-header h1, .customization-panel h3, .dashboard-card h3 {
    color: #f0f6fc !important;
  }

  .project-description, .customization-group h4 {
    color: #8b949e !important;
  }

  .refresh-btn, .customize-btn, .customization-group select {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .refresh-btn:hover, .customize-btn:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
  }

  .checkbox-label {
    color: #c9d1d9;
  }

  .error-message {
    background: #490202 !important;
    color: #f85149 !important;
  }

  .retry-btn {
    background: #da3633 !important;
  }

  .loading-state {
    color: #8b949e !important;
  }

  .activity-item, .deadline-item {
    background: #0d1117 !important;
    border-color: #21262d !important;
  }

  .activity-item:hover, .deadline-item:hover {
    background: #21262d !important;
    border-color: #30363d !important;
  }

  .activity-user {
    color: #58a6ff !important;
  }

  .activity-action, .deadline-assignee {
    color: #8b949e !important;
  }

  .activity-item-name, .deadline-title {
    color: #c9d1d9 !important;
  }

  .activity-time, .no-activity {
    color: #6e7681 !important;
  }

  .deadline-key {
    color: #f0a020 !important;
  }

  .stat-number {
    color: #58a6ff !important;
  }

  .stat-label {
    color: #8b949e !important;
  }

  .progress-bar {
    background: #21262d !important;
  }

  .progress-fill {
    background: #238636 !important;
  }

  .progress-text {
    color: #8b949e !important;
  }

  .no-projects-message {
    color: #8b949e !important;
  }

  .create-btn {
    background: #238636 !important;
    border-color: #238636 !important;
  }

  .create-btn:hover {
    background: #2ea043 !important;
    border-color: #2ea043 !important;
  }
}

[data-theme="light"] {
  .home-view {
    background: #f8f9fa;
  }

  .dashboard-header, .customization-panel, .dashboard-card {
    background: white !important;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
  }

  .dashboard-header h1, .customization-panel h3, .dashboard-card h3 {
    color: #333 !important;
  }

  .project-description, .customization-group h4 {
    color: #666 !important;
  }

  .refresh-btn, .customize-btn, .customization-group select {
    background: white !important;
    border-color: #ddd !important;
    color: #333 !important;
  }

  .refresh-btn:hover, .customize-btn:hover {
    background: #f8f9fa !important;
    border-color: #0066cc !important;
  }

  .checkbox-label {
    color: #333;
  }

  .error-message {
    background: #f8d7da !important;
    color: #721c24 !important;
  }

  .retry-btn {
    background: #dc3545 !important;
  }

  .loading-state {
    color: #666 !important;
  }

  .activity-item, .deadline-item {
    background: #f8f9fa !important;
    border-color: #e9ecef !important;
  }

  .activity-item:hover, .deadline-item:hover {
    background: #e9ecef !important;
    border-color: #dee2e6 !important;
  }

  .activity-user {
    color: #0066cc !important;
  }

  .activity-action, .deadline-assignee {
    color: #666 !important;
  }

  .activity-item-name, .deadline-title {
    color: #333 !important;
  }

  .activity-time, .no-activity {
    color: #999 !important;
  }

  .deadline-key {
    color: #856404 !important;
  }

  .stat-number {
    color: #0066cc !important;
  }

  .stat-label {
    color: #666 !important;
  }

  .progress-bar {
    background: #e9ecef !important;
  }

  .progress-fill {
    background: #28a745 !important;
  }

  .progress-text {
    color: #666 !important;
  }

  .no-projects-message {
    color: #666 !important;
  }

  .create-btn {
    background: #0066cc !important;
    border-color: #0066cc !important;
  }

  .create-btn:hover {
    background: #0056b3 !important;
    border-color: #0056b3 !important;
  }
}
</style>