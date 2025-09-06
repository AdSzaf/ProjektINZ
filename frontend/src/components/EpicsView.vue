<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AddEpicView from './AddEpicView.vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

const projectStore = useProjectStore()
const showAddEpicModal = ref(false)
const currentProject = computed(() => projectStore.selectedProject)

const epics = ref([])
const issues = ref([])
const issueTypes = ref([])
const viewMode = ref('board')
const expandedEpics = ref([])

const handleEpicCreated = () => {
  showAddEpicModal.value = false
  fetchEpics()
}

const fetchEpics = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/epics/`)
  epics.value = res.data
}

const fetchIssues = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/`)
  issues.value = res.data
}

const fetchIssueTypes = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get('/api/issue-types/')
  issueTypes.value = res.data
}

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

const getIssueTypeIcon = (typeId) => {
  const type = issueTypes.value.find(t => t.id === String(typeId))
  return type ? type.icon : '📝'
}

const getIssueTypeCounts = (issues) => {
  return issues.reduce((counts, issue) => {
    counts[issue.type] = (counts[issue.type] || 0) + 1
    return counts
  }, {})
}

const getIssuesForEpic = (epicId) => {
  return issues.value.filter(issue => issue.epic === epicId)
}

const getEpicProgress = (epicId) => {
  const epicIssues = getIssuesForEpic(epicId)
  if (!epicIssues.length) return 0
  const doneCount = epicIssues.filter(i => i.status === 'done' || i.status === 'Done').length
  return Math.round((doneCount / epicIssues.length) * 100)
}

onMounted(() => {
  fetchEpics()
  fetchIssues()
  fetchIssueTypes()
})
watch(currentProject, () => {
  fetchEpics()
  fetchIssues()
  fetchIssueTypes()
})
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
            <span class="epic-key">{{ epic.key || epic.id.slice(0, 8) }}</span>
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
                  :style="{ width: `${getEpicProgress(epic.id)}%` }"
                ></div>
              </div>
              <span class="progress-text">{{ getEpicProgress(epic.id) }}%</span>
            </div>
          </div>
        </div>

        <!-- Epic Issues -->
        <div class="epic-issues">
          <div class="issues-header">
            <span class="issues-count">{{ getIssuesForEpic(epic.id).length }} issues</span>
            <button class="btn-link" @click="toggleIssues(epic.id)">
              {{ expandedEpics.includes(epic.id) ? 'Collapse' : 'View All' }}
            </button>
          </div>
          
          <div 
            v-if="expandedEpics.includes(epic.id) || getIssuesForEpic(epic.id).length <= 3"
            class="issues-list"
          >
            <div 
              v-for="issue in (expandedEpics.includes(epic.id) ? getIssuesForEpic(epic.id) : getIssuesForEpic(epic.id).slice(0, 3))" 
              :key="issue.id"
              class="issue-item"
              :class="`issue-${issue.issue_type}`"
            >
              <div class="issue-info">
                <span class="issue-key">{{ issue.key }}</span>
                <span class="issue-title">{{ issue.title }}</span>
              </div>
              <div class="issue-meta">
                <span class="issue-type" :class="`type-${issue.issue_type}`">
                  {{ getIssueTypeIcon(issue.issue_type) }}
                </span>
                <span class="issue-status" :class="`status-${issue.status.toLowerCase()}`">
                  {{ issue.status }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="issues-summary">
            <div class="issue-type-counts">
              <span v-for="(count, type) in getIssueTypeCounts(getIssuesForEpic(epic.id))" 
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

/* Add this to your existing <style scoped> section */

@media (prefers-color-scheme: dark) {
  /* Page Header */
  .page-header h1 {
    color: #f0f6fc !important;
  }

  .page-description {
    color: #8b949e !important;
  }

  /* Buttons */
  .btn-primary {
    background: #238636 !important;
    color: #ffffff !important;
  }

  .btn-primary:hover {
    background: #2ea043 !important;
  }

  .btn-secondary {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border-color: #30363d !important;
  }

  .btn-secondary:hover {
    background: #30363d !important;
  }

  .btn-link {
    color: #58a6ff !important;
  }

  .btn-link:hover {
    color: #79c0ff !important;
  }

  /* Epic Cards */
  .epic-card {
    background: #161b22 !important;
    border-color: #30363d !important;
    box-shadow: 0 2px 4px rgba(1, 4, 9, 0.3);
  }

  .epic-card:hover {
    box-shadow: 0 8px 16px rgba(1, 4, 9, 0.4) !important;
  }

  .epic-card.status-completed {
    border-left-color: #238636 !important;
  }

  .epic-card.status-in-progress {
    border-left-color: #58a6ff !important;
  }

  .epic-card.status-planning {
    border-left-color: #d29922 !important;
  }

  .epic-card.status-todo {
    border-left-color: #6e7681 !important;
  }

  /* Epic Header */
  .epic-header {
    background: #0d1117 !important;
    border-color: #30363d !important;
  }

  .epic-key {
    background: #58a6ff !important;
    color: #ffffff !important;
  }

  .epic-title {
    color: #f0f6fc !important;
  }

  /* Epic Status Badges */
  .epic-status.status-completed {
    background: #1b2718 !important;
    color: #7ee787 !important;
  }

  .epic-status.status-in-progress {
    background: #1a2332 !important;
    color: #79c0ff !important;
  }

  .epic-status.status-planning {
    background: #2d2408 !important;
    color: #f0cc81 !important;
  }

  .epic-status.status-todo {
    background: #21262d !important;
    color: #8b949e !important;
  }

  /* Progress Bar */
  .progress-bar {
    background: #21262d !important;
    border: 1px solid #30363d;
    overflow: hidden;
  }

  .progress-fill {
    background: #238636 !important;
    box-shadow: 0 2px 4px rgba(35, 134, 54, 0.4);
    position: relative;
    overflow: hidden;
  }

  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    animation: shimmer 2s infinite;
  }

  .progress-text {
    color: #8b949e !important;
  }

  /* Epic Issues Section */
  .epic-issues {
    background: #161b22 !important;
  }

  .issues-count {
    color: #8b949e !important;
  }

  /* Issue Items */
  .issue-item {
    background: #0d1117 !important;
    border: 1px solid #21262d;
    transition: all 0.2s ease;
  }

  .issue-item:hover {
    background: #21262d !important;
    border-color: #30363d !important;
    transform: translateX(4px);
  }

  .issue-item.issue-task {
    border-left-color: #58a6ff !important;
  }

  .issue-item.issue-bug {
    border-left-color: #ff7b72 !important;
  }

  .issue-item.issue-subtask {
    border-left-color: #7ee787 !important;
  }

  .issue-key {
    color: #8b949e !important;
  }

  .issue-title {
    color: #c9d1d9 !important;
  }

  /* Issue Status Badges */
  .issue-status.status-done {
    background: #1b2718 !important;
    color: #7ee787 !important;
  }

  .issue-status.status-in-progress {
    background: #1a2332 !important;
    color: #79c0ff !important;
  }

  .issue-status.status-to-do {
    background: #21262d !important;
    color: #8b949e !important;
  }

  /* Issues Summary */
  .issues-summary {
    background: #0d1117 !important;
    border: 1px solid #30363d;
  }

  .type-count {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d;
  }

  /* Enhanced interactions and animations */
  .epic-card {
    transition: all 0.3s ease;
    backdrop-filter: blur(8px);
  }

  .epic-card:hover {
    border-color: #484f58 !important;
    transform: translateY(-4px) !important;
  }

  .issue-item {
    position: relative;
  }

  .issue-item:hover .issue-title {
    color: #f0f6fc !important;
  }

  .issue-item:hover .issue-key {
    color: #58a6ff !important;
  }

  /* Type icons with better visibility */
  .issue-type {
    filter: brightness(1.2);
    text-shadow: 0 0 4px rgba(255, 255, 255, 0.3);
  }

  /* Progress animation */
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  /* Epic key hover effect */
  .epic-key {
    transition: all 0.2s ease;
  }

  .epic-card:hover .epic-key {
    background: #79c0ff !important;
    transform: scale(1.05);
  }

  /* Status badges hover effects */
  .epic-status, .issue-status {
    transition: all 0.2s ease;
  }

  .epic-status:hover, .issue-status:hover {
    transform: scale(1.05);
    filter: brightness(1.1);
  }

  /* Button focus states for accessibility */
  .btn-primary:focus,
  .btn-secondary:focus,
  .btn-link:focus {
    outline: 2px solid #58a6ff;
    outline-offset: 2px;
  }

  /* Card focus states */
  .epic-card:focus-within {
    outline: 2px solid #58a6ff;
    outline-offset: 2px;
  }

  /* Improved contrast for better readability */
  .epic-header {
    border-bottom: 1px solid #30363d !important;
  }

  /* Type count badges enhancement */
  .type-count {
    transition: all 0.2s ease;
  }

  .type-count:hover {
    background: #30363d !important;
    transform: scale(1.05);
  }

  /* Subtle gradient backgrounds */
  .epic-card {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%) !important;
  }

  .epic-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important;
  }

  .issue-item {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important;
  }

  .issues-summary {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important;
  }

  /* Enhanced scrollbar styling */
  .epics-view::-webkit-scrollbar {
    width: 8px;
  }

  .epics-view::-webkit-scrollbar-track {
    background: #0d1117;
  }

  .epics-view::-webkit-scrollbar-thumb {
    background: #484f58;
    border-radius: 4px;
  }

  .epics-view::-webkit-scrollbar-thumb:hover {
    background: #6e7681;
  }
}
</style>