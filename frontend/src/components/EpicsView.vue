<script setup>
import { ref, computed } from 'vue'
import AddEpicView from './AddEpicView.vue'

const showAddEpicModal = ref(false)

const handleEpicCreated = () => {
  showAddEpicModal.value = false
  // TODO: fetchEpics() here to refresh the epics list from backend
}

// Mock data - replace with real API calls
const epics = ref([
  {
    id: 1,
    key: 'EP-1',
    title: 'User Authentication System',
    status: 'in-progress',
    progress: 65,
    issues: [
      { id: 1, key: 'TSK-101', title: 'Login page design', type: 'task', status: 'Done' },
      { id: 2, key: 'TSK-102', title: 'JWT implementation', type: 'task', status: 'In Progress' },
      { id: 3, key: 'BUG-45', title: 'Password reset not working', type: 'bug', status: 'To Do' },
      { id: 4, key: 'SUB-12', title: 'Email validation', type: 'subtask', status: 'Done' }
    ]
  },
  {
    id: 2,
    key: 'EP-2',
    title: 'Dashboard Analytics',
    status: 'planning',
    progress: 25,
    issues: [
      { id: 5, key: 'TSK-201', title: 'Chart component library', type: 'task', status: 'In Progress' },
      { id: 6, key: 'TSK-202', title: 'Data aggregation API', type: 'task', status: 'To Do' },
      { id: 7, key: 'SUB-20', title: 'Performance metrics', type: 'subtask', status: 'To Do' }
    ]
  },
  {
    id: 3,
    key: 'EP-3',
    title: 'Mobile Responsive Design',
    status: 'completed',
    progress: 100,
    issues: [
      { id: 8, key: 'TSK-301', title: 'Mobile navigation', type: 'task', status: 'Done' },
      { id: 9, key: 'TSK-302', title: 'Touch interactions', type: 'task', status: 'Done' },
      { id: 10, key: 'BUG-67', title: 'Sidebar not responsive', type: 'bug', status: 'Done' }
    ]
  },
  {
    id: 4,
    key: 'EP-4',
    title: 'API Documentation',
    status: 'todo',
    progress: 0,
    issues: [
      { id: 11, key: 'TSK-401', title: 'Swagger setup', type: 'task', status: 'To Do' },
      { id: 12, key: 'TSK-402', title: 'Endpoint documentation', type: 'task', status: 'To Do' },
      { id: 13, key: 'SUB-30', title: 'API examples', type: 'subtask', status: 'To Do' },
      { id: 14, key: 'TSK-403', title: 'Authentication docs', type: 'task', status: 'To Do' },
      { id: 15, key: 'SUB-31', title: 'Error handling guide', type: 'subtask', status: 'To Do' }
    ]
  }
])

const viewMode = ref('board')
const expandedEpics = ref([])

const toggleView = () => {
  viewMode.value = viewMode.value === 'board' ? 'list' : 'board'
}

const createEpic = () => {
  console.log('Creating new epic...')
}

const toggleIssues = (epicId) => {
  const index = expandedEpics.value.indexOf(epicId)
  if (index > -1) {
    expandedEpics.value.splice(index, 1)
  } else {
    expandedEpics.value.push(epicId)
  }
}

const getIssueTypeIcon = (type) => {
  const icons = {
    task: '📝',
    bug: '🐛',
    subtask: '🔸',
    story: '📖'
  }
  return icons[type] || '📝'
}

const getIssueTypeCounts = (issues) => {
  return issues.reduce((counts, issue) => {
    counts[issue.type] = (counts[issue.type] || 0) + 1
    return counts
  }, {})
}
</script>

<template>
  <div class="epics-view">
    <!-- Page Header -->
    <div class="page-header">
      <h1>Epics</h1>
      <p class="page-description">Manage and track your project epics and their associated issues</p>
      <div class="header-actions">
        <button class="btn-secondary" @click="toggleView">
          {{ viewMode === 'board' ? '📋 List View' : '🏠 Board View' }}
        </button>
        <button class="btn-primary" @click="showAddEpicModal = true">
          + Create Epic
        </button>
      </div>
    </div>

    <!-- Epics Board -->
    <div class="epics-board">
      <div 
        v-for="epic in epics" 
        :key="epic.id"
        class="epic-card"
        :class="`status-${epic.status}`"
      >
        <!-- Epic Header -->
        <div class="epic-header">
          <div class="epic-title-row">
            <span class="epic-key">{{ epic.key }}</span>
            <h3 class="epic-title">{{ epic.title }}</h3>
          </div>
          <div class="epic-meta">
            <span class="epic-status" :class="`status-${epic.status}`">
              {{ epic.status.toUpperCase() }}
            </span>
            <div class="epic-progress">
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${epic.progress}%` }"
                ></div>
              </div>
              <span class="progress-text">{{ epic.progress }}%</span>
            </div>
          </div>
        </div>

        <!-- Epic Issues -->
        <div class="epic-issues">
          <div class="issues-header">
            <span class="issues-count">{{ epic.issues.length }} issues</span>
            <button class="btn-link" @click="toggleIssues(epic.id)">
              {{ expandedEpics.includes(epic.id) ? 'Collapse' : 'View All' }}
            </button>
          </div>
          
          <div 
            v-if="expandedEpics.includes(epic.id) || epic.issues.length <= 3"
            class="issues-list"
          >
            <div 
              v-for="issue in (expandedEpics.includes(epic.id) ? epic.issues : epic.issues.slice(0, 3))" 
              :key="issue.id"
              class="issue-item"
              :class="`issue-${issue.type}`"
            >
              <div class="issue-info">
                <span class="issue-key">{{ issue.key }}</span>
                <span class="issue-title">{{ issue.title }}</span>
              </div>
              <div class="issue-meta">
                <span class="issue-type" :class="`type-${issue.type}`">
                  {{ getIssueTypeIcon(issue.type) }}
                </span>
                <span class="issue-status" :class="`status-${issue.status.toLowerCase()}`">
                  {{ issue.status }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="issues-summary">
            <div class="issue-type-counts">
              <span v-for="(count, type) in getIssueTypeCounts(epic.issues)" 
                    :key="type" 
                    class="type-count"
                    :class="`type-${type}`">
                {{ getIssueTypeIcon(type) }} {{ count }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <AddEpicView
    :showModal="showAddEpicModal"
    @close="showAddEpicModal = false"
    @save="handleEpicCreated"
    />
  </div>
</template>

<style scoped>
.epics-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.page-header h1 {
  margin: 0;
  color: #333;
  font-size: 2rem;
}

.page-description {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn-primary, .btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #0066cc;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.btn-link {
  background: none;
  border: none;
  color: #0066cc;
  cursor: pointer;
  font-size: 0.9rem;
  text-decoration: underline;
}

.btn-link:hover {
  color: #0056b3;
}

.epics-board {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  flex: 1;
  align-content: start;
}

.epic-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e1e5e9;
  overflow: hidden;
  transition: all 0.2s;
  height: fit-content;
}

.epic-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.epic-card.status-completed {
  border-left: 4px solid #28a745;
}

.epic-card.status-in-progress {
  border-left: 4px solid #0066cc;
}

.epic-card.status-planning {
  border-left: 4px solid #ffc107;
}

.epic-card.status-todo {
  border-left: 4px solid #6c757d;
}

.epic-header {
  padding: 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e5e9;
}

.epic-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.epic-key {
  background: #0066cc;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: bold;
  flex-shrink: 0;
}

.epic-title {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
  font-weight: 600;
}

.epic-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.epic-status {
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: bold;
  text-transform: uppercase;
}

.epic-status.status-completed {
  background: #d4edda;
  color: #155724;
}

.epic-status.status-in-progress {
  background: #d1ecf1;
  color: #0c5460;
}

.epic-status.status-planning {
  background: #fff3cd;
  color: #856404;
}

.epic-status.status-todo {
  background: #e2e3e5;
  color: #383d41;
}

.epic-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar {
  width: 60px;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #28a745;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
  min-width: 30px;
}

.epic-issues {
  padding: 1.5rem;
}

.issues-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.issues-count {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.issue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid transparent;
  transition: all 0.2s;
}

.issue-item:hover {
  background: #e9ecef;
  cursor: pointer;
}

.issue-item.issue-task {
  border-left-color: #0066cc;
}

.issue-item.issue-bug {
  border-left-color: #e74c3c;
}

.issue-item.issue-subtask {
  border-left-color: #17a2b8;
}

.issue-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.issue-key {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
}

.issue-title {
  font-size: 0.9rem;
  color: #333;
}

.issue-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.issue-type {
  font-size: 1rem;
}

.issue-status {
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
}

.issue-status.status-done {
  background: #d4edda;
  color: #155724;
}

.issue-status.status-in-progress {
  background: #d1ecf1;
  color: #0c5460;
}

.issue-status.status-to-do {
  background: #e2e3e5;
  color: #383d41;
}

.issues-summary {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  text-align: center;
}

.issue-type-counts {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.type-count {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: white;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 768px) {
  .epics-board {
    grid-template-columns: 1fr;
  }
  
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .issue-item {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }
  
  .issue-meta {
    justify-content: space-between;
  }
}
</style>