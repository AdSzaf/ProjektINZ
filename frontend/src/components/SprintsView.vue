<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

// Data
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const sprints = ref([])
const sprintIssues = ref({})
const issueTypes = ref([])
const userCache = ref({})
const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const sortBy = ref('created_date')
const sortOrder = ref('desc')

// Computed properties
const filteredSprints = computed(() => {
  let filtered = [...sprints.value]

  // Filter by status
  if (filterStatus.value) {
    filtered = filtered.filter(sprint => sprint.status === filterStatus.value)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(sprint => 
      sprint.name.toLowerCase().includes(query) ||
      (sprint.description && sprint.description.toLowerCase().includes(query))
    )
  }

  // Sort sprints
  filtered.sort((a, b) => {
    let aValue = a[sortBy.value]
    let bValue = b[sortBy.value]
    
    if (sortBy.value.includes('date')) {
      aValue = new Date(aValue)
      bValue = new Date(bValue)
    }
    
    if (sortOrder.value === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })

  return filtered
})

const sprintStatuses = computed(() => {
  const statuses = [...new Set(sprints.value.map(s => s.status))]
  return statuses
})

// Methods
const getIssueTypeIcon = (typeId) => {
  const type = issueTypes.value.find(t => t.id === String(typeId) || t.id === typeId)
  return type ? type.icon : '📝'
}

const getPriorityIcon = (priority) => {
  const icons = {
    highest: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '🟢',
    lowest: '🔵'
  }
  return icons[priority] || '🟡'
}

const getSprintProgress = (sprintId) => {
  const issues = sprintIssues.value[sprintId] || []
  if (!issues.length) return 0
  const doneCount = issues.filter(i => i.status === 'done' || i.status === 'Done').length
  return Math.round((doneCount / issues.length) * 100)
}

const getSprintStoryPoints = (sprintId) => {
  const issues = sprintIssues.value[sprintId] || []
  return issues.reduce((total, issue) => total + (issue.storyPoints || issue.story_points || 0), 0)
}

const getCompletedStoryPoints = (sprintId) => {
  const issues = sprintIssues.value[sprintId] || []
  const completedIssues = issues.filter(i => i.status === 'done' || i.status === 'Done')
  return completedIssues.reduce((total, issue) => total + (issue.storyPoints || issue.story_points || 0), 0)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

const formatDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) return ''
  return `${formatDate(startDate)} - ${formatDate(endDate)}`
}

const getDaysRemaining = (endDate) => {
  if (!endDate) return null
  const today = new Date()
  const end = new Date(endDate)
  const diffTime = end - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}

const getSprintDuration = (startDate, endDate) => {
  if (!startDate || !endDate) return 0
  const start = new Date(startDate)
  const end = new Date(endDate)
  const diffTime = end - start
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}

const fetchSprints = async () => {
  if (!currentProject.value?.id) return
  
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    const res = await axios.get(`/api/projects/${currentProject.value.id}/sprints/`)
    sprints.value = res.data
    
    // Fetch issues for each sprint
    await Promise.all(sprints.value.map(sprint => fetchSprintIssues(sprint.id)))
  } catch (error) {
    console.error('Failed to fetch sprints:', error)
  } finally {
    loading.value = false
  }
}

const fetchSprintIssues = async (sprintId) => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/?sprint=${sprintId}`, {
      headers: { Authorization: `Token ${token}` }
    })
    // Backend currently returns all project issues; filter client-side by sprint
    const issuesForSprint = (res.data || []).filter(issue => {
      const issueSprintId = typeof issue.sprint === 'string' ? issue.sprint : issue.sprint?.id
      return String(issueSprintId || '') === String(sprintId)
    })
    sprintIssues.value[sprintId] = issuesForSprint
    
    // Cache user data for assignees
    issuesForSprint.forEach(issue => {
      if (issue.assignee && !userCache.value[issue.assignee]) {
        fetchUserShort(issue.assignee)
      }
    })
  } catch (error) {
    console.error(`Failed to fetch issues for sprint ${sprintId}:`, error)
    sprintIssues.value[sprintId] = []
  }
}

const fetchIssueTypes = async () => {
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    const res = await axios.get('/api/issue-types/')
    issueTypes.value = res.data
  } catch (error) {
    console.error('Failed to fetch issue types:', error)
  }
}

const fetchUserShort = async (userId) => {
  if (!userId || userCache.value[userId]) return userCache.value[userId]
  
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`/api/users/${userId}/short/`, {
      headers: { Authorization: `Token ${token}` }
    })
    userCache.value[userId] = res.data
    return res.data
  } catch (error) {
    console.error(`Failed to fetch user ${userId}:`, error)
    return null
  }
}

const getStatusBadgeClass = (status) => {
  const statusClasses = {
    'future': 'status-future',
    'active': 'status-active',
    'completed': 'status-completed',
    'cancelled': 'status-cancelled'
  }
  return statusClasses[status] || 'status-future'
}

// Lifecycle
onMounted(() => {
  fetchSprints()
  fetchIssueTypes()
})

watch(currentProject, () => {
  if (currentProject.value) {
    fetchSprints()
    fetchIssueTypes()
  }
})
</script>

<template>
  <div v-if="!currentProject" class="no-projects-message">
    <h2>No projects found</h2>
    <p>Create your first project to get started!</p>
    <button class="btn btn-primary" @click="$router.push('/create-project')">+ Create Project</button>
  </div>
  <div v-else class="sprint-view">
    <div class="page-header">
      <div class="header-content">
        <h1>Sprints</h1>
        <p class="page-description">View all sprints and their progress</p>
      </div>
    </div>

    <div class="sprint-filters">
      <div class="filter-group">
        <input 
          type="text" 
          v-model="searchQuery"
          placeholder="Search sprints..."
          class="search-input"
        />
        
        <select v-model="filterStatus" class="filter-select">
          <option value="">All Statuses</option>
          <option v-for="status in sprintStatuses" :key="status" :value="status">
            {{ status.charAt(0).toUpperCase() + status.slice(1) }}
          </option>
        </select>
      </div>
      
      <div class="sort-options">
        <select v-model="sortBy" class="sort-select">
          <option value="created_date">Created Date</option>
          <option value="start_date">Start Date</option>
          <option value="end_date">End Date</option>
          <option value="name">Name</option>
        </select>
        
        <button 
          class="sort-order-btn"
          @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
          :title="sortOrder === 'asc' ? 'Sort Descending' : 'Sort Ascending'"
        >
          {{ sortOrder === 'asc' ? '⬆️' : '⬇️' }}
        </button>
      </div>
    </div>

    <div class="sprint-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">🔄</div>
        <p>Loading sprints...</p>
      </div>

      <div v-else-if="filteredSprints.length === 0" class="empty-state">
        <div class="empty-icon">📅</div>
        <h3>No Sprints Found</h3>
        <p>{{ sprints.length === 0 ? 'No sprints have been created yet.' : 'No sprints match your current filters.' }}</p>
      </div>

      <div v-else class="sprints-grid">
        <div 
          v-for="sprint in filteredSprints" 
          :key="sprint.id"
          class="sprint-card"
        >
          <div class="sprint-card-header">
            <div class="sprint-title-section">
              <h3 class="sprint-name">{{ sprint.name }}</h3>
              <span class="sprint-status" :class="getStatusBadgeClass(sprint.status)">
                {{ sprint.status.charAt(0).toUpperCase() + sprint.status.slice(1) }}
              </span>
            </div>
            
            <div class="sprint-dates">
              <span class="date-range">{{ formatDateRange(sprint.start_date, sprint.end_date) }}</span>
              <span v-if="sprint.status === 'active'" class="days-remaining">
                {{ getDaysRemaining(sprint.end_date) }} days remaining
              </span>
              <span v-else-if="sprint.status === 'future'" class="duration">
                {{ getSprintDuration(sprint.start_date, sprint.end_date) }} days duration
              </span>
            </div>
          </div>

          <div class="sprint-description" v-if="sprint.description">
            <p>{{ sprint.description }}</p>
          </div>

          <div class="sprint-stats">
            <div class="stat-item">
              <span class="stat-label">Issues:</span>
              <span class="stat-value">{{ (sprintIssues[sprint.id] || []).length }}</span>
            </div>
            
            <div class="stat-item">
              <span class="stat-label">Story Points:</span>
              <span class="stat-value">
                {{ getCompletedStoryPoints(sprint.id) }} / {{ getSprintStoryPoints(sprint.id) }}
              </span>
            </div>
            
            <div class="stat-item">
              <span class="stat-label">Progress:</span>
              <span class="stat-value">{{ getSprintProgress(sprint.id) }}%</span>
            </div>
          </div>

          <div class="progress-section">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${getSprintProgress(sprint.id)}%` }"
              ></div>
            </div>
          </div>

          <div class="sprint-issues-section" v-if="sprintIssues[sprint.id]?.length > 0">
            <h4 class="issues-title">Issues ({{ sprintIssues[sprint.id].length }})</h4>
            <div class="issues-list">
              <div 
                v-for="issue in sprintIssues[sprint.id]" 
                :key="issue.id"
                class="issue-item"
              >
                <div class="issue-header">
                  <span class="issue-key">{{ issue.key }}</span>
                  <span class="issue-type">{{ getIssueTypeIcon(issue.issue_type) }}</span>
                  <span class="issue-priority">{{ getPriorityIcon(issue.priority) }}</span>
                </div>
                
                <div class="issue-title">{{ issue.title }}</div>
                
                <div class="issue-meta">
                  <span class="issue-status" :class="`status-${issue.status?.toLowerCase()}`">
                    {{ issue.status }}
                  </span>
                  <span class="issue-assignee" v-if="issue.assignee && userCache[issue.assignee]">
                    {{ userCache[issue.assignee].initials }}
                  </span>
                  <span class="issue-story-points" v-if="issue.storyPoints || issue.story_points">
                    {{ issue.storyPoints || issue.story_points }} SP
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-sprint-issues">
            <p>No issues in this sprint</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sprint-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
}

.page-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e1e5e9;
}

.header-content h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2rem;
}

.page-description {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.sprint-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-group {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input,
.filter-select,
.sort-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  outline: none;
  font-size: 0.9rem;
}

.search-input:focus,
.filter-select:focus,
.sort-select:focus {
  border-color: #0066cc;
}

.search-input {
  width: 250px;
}

.sort-options {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.sort-order-btn {
  padding: 0.5rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.sort-order-btn:hover {
  background: #e9ecef;
}

.sprint-content {
  flex: 1;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
}

.loading-spinner {
  font-size: 2rem;
  margin-bottom: 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.sprints-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.sprint-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  transition: box-shadow 0.2s, transform 0.2s;
}

.sprint-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.sprint-card-header {
  margin-bottom: 1rem;
}

.sprint-title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.sprint-name {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.sprint-status {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-future {
  background: #e6f2ff;
  color: #0066cc;
}

.status-active {
  background: #d4edda;
  color: #28a745;
}

.status-completed {
  background: #f8f9fa;
  color: #6c757d;
}

.status-cancelled {
  background: #f8d7da;
  color: #dc3545;
}

.sprint-dates {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.date-range {
  color: #666;
  font-size: 0.9rem;
}

.days-remaining {
  color: #28a745;
  font-size: 0.8rem;
  font-weight: 500;
}

.duration {
  color: #666;
  font-size: 0.8rem;
}

.sprint-description {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #0066cc;
}

.sprint-description p {
  margin: 0;
  color: #555;
  font-size: 0.9rem;
  line-height: 1.4;
}

.sprint-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.progress-section {
  margin-bottom: 1.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e1e5e9;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0066cc, #4ea1ff);
  transition: width 0.3s ease;
}

.sprint-issues-section {
  border-top: 1px solid #e1e5e9;
  padding-top: 1rem;
}

.issues-title {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.issue-item {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e1e5e9;
  transition: background-color 0.2s;
}

.issue-item:hover {
  background: #e9ecef;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.issue-key {
  background: #e6f2ff;
  color: #0066cc;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
}

.issue-type,
.issue-priority {
  font-size: 0.9rem;
}

.issue-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  line-height: 1.3;
}

.issue-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.issue-status {
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-todo,
.status-to-do {
  background: #f8f9fa;
  color: #6c757d;
}

.status-in-progress,
.status-in_progress {
  background: #fff3cd;
  color: #856404;
}

.status-done {
  background: #d4edda;
  color: #155724;
}

.issue-assignee {
  background: #0066cc;
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: bold;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-transform: uppercase;
}

.issue-story-points {
  background: #28a745;
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: bold;
}

.empty-sprint-issues {
  border-top: 1px solid #e1e5e9;
  padding-top: 1rem;
  text-align: center;
  color: #666;
  font-style: italic;
}


@media (max-width: 768px) {
  .sprint-view {
    padding: 1rem;
  }
  
  .sprint-filters {
    flex-direction: column;
    gap: 1rem;
  }
  
  .filter-group {
    flex-wrap: wrap;
  }
  
  .search-input {
    width: 200px;
  }
  
  .sprints-grid {
    grid-template-columns: 1fr;
  }
  
  .sprint-stats {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .stat-item {
    flex-direction: row;
    justify-content: space-between;
  }
}


@media (prefers-color-scheme: dark) {
  .sprint-view,
  .sprint-filters,
  .sprint-card,
  .sprint-description,
  .sprint-stats,
  .issue-item {
    background: #181a1b !important;
    color: #f3f3f3 !important;
    border-color: #333 !important;
  }
  
  .page-header,
  .header-content h1,
  .page-description,
  .sprint-name,
  .date-range,
  .stat-label,
  .stat-value,
  .issues-title,
  .issue-title,
  .empty-state h3 {
    color: #f3f3f3 !important;
  }
  
  .search-input,
  .filter-select,
  .sort-select,
  .sort-order-btn {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }
  
  .sort-order-btn:hover {
    background: #333 !important;
  }
  
  .sprint-description {
    background: #232526 !important;
    border-left-color: #4ea1ff !important;
  }
  
  .sprint-description p {
    color: #ccc !important;
  }
  
  .sprint-stats {
    background: #232526 !important;
  }
  
  .issue-item:hover {
    background: #232526 !important;
  }
  
  .issue-key {
    background: #232526 !important;
    color: #4ea1ff !important;
  }
  
  .status-future {
    background: #1a2332 !important;
    color: #4ea1ff !important;
  }
  
  .status-active {
    background: #1e3a26 !important;
    color: #4ade80 !important;
  }
  
  .status-completed {
    background: #232526 !important;
    color: #aaa !important;
  }
  
  .status-cancelled {
    background: #3a1f1f !important;
    color: #f87171 !important;
  }
  
  .status-todo,
  .status-to-do {
    background: #232526 !important;
    color: #aaa !important;
  }
  
  .status-in-progress,
  .status-in_progress {
    background: #3a3017 !important;
    color: #fbbf24 !important;
  }
  
  .status-done {
    background: #1e3a26 !important;
    color: #4ade80 !important;
  }
  
  .progress-bar {
    background: #333 !important;
  }
  
  .progress-fill {
    background: linear-gradient(90deg, #4ea1ff, #0066cc) !important;
  }
  
  .days-remaining {
    color: #4ade80 !important;
  }
  
  .duration,
  .empty-sprint-issues {
    color: #aaa !important;
  }
  
  .loading-state,
  .empty-state {
    color: #aaa !important;
  }
}</style>