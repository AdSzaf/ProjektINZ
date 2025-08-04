<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'

const projectStore = useProjectStore()
const selectedProject = computed(() => projectStore.selectedProject)
const currentProject = computed(() => projectStore.selectedProject)

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
</script>

<template>
  <div>
    <div class="dashboard-header">
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

    <!-- Dashboard Cards -->
    <div v-if="selectedProject" class="dashboard-grid">
      <!-- Sprint Progress Card -->
      <div class="dashboard-card">
        <h3>{{ dashboardData.activeSprintName }} Progress</h3>
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

      <!-- Quick Stats -->
      <div class="dashboard-card stats-card">
        <h3>Quick Stats</h3>
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
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="dashboard-card activity-card">
        <h3>Recent Activity</h3>
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
        </div>
      </div>
    </div>
    <div v-else class="no-projects-message">
      <p>You have no projects yet.</p>
      <button class="create-btn" @click="$router.push('/create-project')">
        + Create Project
      </button>
    </div>
  </div>
</template>

<style scoped>
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

/* Responsive */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .activity-card {
    grid-column: span 1;
  }
}
</style>