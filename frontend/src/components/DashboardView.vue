<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import AddIssueView from './AddIssueView.vue'
import axios from 'axios'

const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const showAddIssueModal = ref(false)
const issues = ref([])
const columns = ref([])
const users = ref([])

const fetchIssues = async () => {
  if (!currentProject.value?.id) {
    issues.value = []
    return
  }
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/`)
  issues.value = res.data
  console.log('Fetched issues:', issues.value)
}

// UI state
const showAddColumn = ref(false)
const newColumnName = ref('')
const draggedIssue = ref(null)
const showIssueModal = ref(false)
const selectedIssue = ref(null)

// Computed properties
const statusMap = {
  to_do: 'todo',
  in_progress: 'inprogress',
  done: 'done'
}

const getIssuesByStatus = (category) => {
  return issues.value.filter(issue => issue.status === category)
}

const getTotalPoints = (status) => {
  return getIssuesByStatus(status).reduce((total, issue) => total + issue.points, 0)
}

const reverseStatusMap = {
  todo: 'to_do',
  inprogress: 'in_progress',
  done: 'done'
}

// Methods
const addColumn = async () => {
  if (newColumnName.value.trim()) {
    const token = localStorage.getItem('token')
    const res = await axios.post(
      `/api/projects/${currentProject.value.id}/workflow-statuses/add/`,
      { name: newColumnName.value, color: '#6f42c1' },
      { headers: { Authorization: `Token ${token}` } }
    )
    columns.value.push(res.data)
    newColumnName.value = ''
    showAddColumn.value = false
  }
}

const fetchColumns = async () => {
  if (!currentProject.value?.id) {
    columns.value = []
    return
  }
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/workflow-statuses/`)
  columns.value = res.data
}

const removeColumn = (columnCategory) => {
  if (columns.value.length <= 1) return
  issues.value.forEach(issue => {
    if (issue.status === columnCategory) {
      issue.status = columns.value[0].category
    }
  })
  columns.value = columns.value.filter(col => col.category !== columnCategory)
}

const openIssueDetails = (issue) => {
  selectedIssue.value = issue
  showIssueModal.value = true
}

const closeIssueModal = () => {
  showIssueModal.value = false
  selectedIssue.value = null
}

// Drag and Drop
const onDragStart = (event, issue) => {
  draggedIssue.value = issue
  event.dataTransfer.effectAllowed = 'move'
}

const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const onDrop = async (event, targetColumnId) => {
  event.preventDefault()
  if (draggedIssue.value && draggedIssue.value.status !== targetColumnId) {
    const newStatus = targetColumnId
    const issueId = draggedIssue.value.id
    // Optimistically update UI
    draggedIssue.value.status = newStatus
    // Send PATCH to backend
    try {
      const token = localStorage.getItem('token')
      console.log('Updating issue status:', issueId, 'to', newStatus)
      await axios.patch(`/api/issues/${issueId}/status/`, { status: newStatus }, {
        headers: { Authorization: `Token ${token}` }
      })
    } catch (e) {
      console.error('Failed to update issue status:', e)
    }
  }
  draggedIssue.value = null
  fetchIssues()
}

const getPriorityColor = (priority) => {
  switch (priority) {
    case 'High': return '#dc3545'
    case 'Medium': return '#fd7e14'
    case 'Low': return '#28a745'
    default: return '#6c757d'
  }
}

const getTypeIcon = (type) => {
  switch (type) {
    case 'Story': return '📖'
    case 'Task': return '✅'
    case 'Bug': return '🐛'
    case 'Epic': return '📚'
    default: return '📄'
  }
}

const onIssueCreated = (issueData) => {
  // Optionally refresh issues or show a toast
  showAddIssueModal.value = false
   fetchIssues()
}

const getAssigneeName = (assigneeId) => {
  if (!assigneeId) return 'Unassigned'
  const user = users.value.find(u => u.id === assigneeId)
  return user ? user.name : 'Unassigned'
}

const fetchUsers = async () => {
  if (!currentProject.value?.id) {
    users.value = []
    return
  }
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/users/`)
  users.value = res.data
}

onMounted(() => {
  fetchColumns()
  fetchIssues()
  fetchUsers()
})
watch(currentProject, () => {
  fetchColumns()
  fetchIssues()
  fetchUsers()
})
</script>

<template>
  <div class="dashboard-container">
    <!-- Header -->
    <div class="dashboard-header">
      <div>
        <h1>Sprint Board</h1>
        <p class="dashboard-subtitle">Drag and drop issues to update their status</p>
      </div>
      
      <button class="add-column-btn" @click="showAddColumn = true">
        + Add Column
      </button>
    </div>

    <!-- Kanban Board -->
    <div class="kanban-board">
      <div 
        v-for="column in columns" 
        :key="column.category"
        class="kanban-column"
        @dragover="onDragOver"
        @drop="onDrop($event, column.category)"
      >
        <!-- Column Header -->
        <div class="column-header" :style="{ borderTopColor: column.color }">
          <div class="column-info">
            <h3 class="column-title">{{ column.name }}</h3>
            <span class="column-count">{{ getIssuesByStatus(column.category).length }}</span>
            <span class="column-points">{{ getTotalPoints(column.category) }} pts</span>
          </div>
          
          <button 
            v-if="columns.length > 1"
            class="remove-column-btn"
            @click="removeColumn(column.category)"
            title="Remove column"
          >
            ×
          </button>
        </div>

        <!-- Issues/Cards -->
        <div class="issues-container">
          <div
            v-for="issue in getIssuesByStatus(column.category)"
            :key="issue.id"
            class="issue-card"
            draggable="true"
            @dragstart="onDragStart($event, issue)"
            @click="openIssueDetails(issue)"
          >
            <!-- Issue Header -->
            <div class="issue-header">
              <span class="issue-id">{{ issue.key }}</span>
              <span class="issue-type">{{ getTypeIcon(issue.issue_type) }}</span>
            </div>

            <!-- Issue Title -->
            <h4 class="issue-title">{{ issue.title }}</h4>

            <!-- Issue Footer -->
            <div class="issue-footer">
              <div class="issue-meta">
                <span 
                  class="priority-badge" 
                  :style="{ backgroundColor: getPriorityColor(issue.priority) }"
                >
                  {{ issue.priority }}
                </span>
                <span class="story-points">{{ issue.points }} pts</span>
              </div>
              
              <div class="assignee-avatar" :title="issue.assignee">
                {{ issue.assignee ? issue.assignee.split(' ').map(n => n[0]).join('') : '' }}
              </div>
            </div>
          </div>

          <!-- Add Issue Button -->
          <button class="add-issue-btn" @click="showAddIssueModal = true">
            + Add Issue
          </button>
        </div>
      </div>
    </div>

    <!-- Add Column Modal -->
    <div v-if="showAddColumn" class="modal-overlay" @click="showAddColumn = false">
      <div class="modal-content" @click.stop>
        <h3>Add New Column</h3>
        <input
          v-model="newColumnName"
          type="text"
          placeholder="Column name"
          @keyup.enter="addColumn"
          class="column-input"
        />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showAddColumn = false">Cancel</button>
          <button class="btn-primary" @click="addColumn">Add Column</button>
        </div>
      </div>
    </div>

    <!-- Issue Details Modal -->
    <div v-if="showIssueModal" class="modal-overlay" @click="closeIssueModal">
      <div class="issue-modal" @click.stop>
        <div class="issue-modal-header">
          <div>
            <h2>{{ selectedIssue?.key }}: {{ selectedIssue?.title }}</h2>
            <div class="issue-modal-meta">
              <span class="issue-type-full">{{ getTypeIcon(selectedIssue?.type) }} {{ selectedIssue?.type }}</span>
              <span 
                class="priority-badge" 
                :style="{ backgroundColor: getPriorityColor(selectedIssue?.priority) }"
              >
                {{ selectedIssue?.priority }}
              </span>
              <span class="story-points-full">{{ selectedIssue?.points }} Story Points</span>
            </div>
          </div>
          <button class="close-btn" @click="closeIssueModal">×</button>
        </div>
        
        <div class="issue-modal-body">
          <div class="issue-field">
            <label>Assignee:</label>
            <span>{{ getAssigneeName(selectedIssue?.assignee) }}</span>
          </div>
          
          <div class="issue-field">
            <label>Status:</label>
            <span>{{ columns.find(c => c.id === selectedIssue?.status)?.name }}</span>
          </div>
          
          <div class="issue-field">
            <label>Description:</label>
            <p>This is a placeholder description for the issue. In a real application, this would contain the full issue description.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <AddIssueView
  :showModal="showAddIssueModal"
  @close="showAddIssueModal = false"
  @save="onIssueCreated"
/>
</template>

<style scoped>
.dashboard-container {
  padding: 2rem;
  height: 100vh;
  overflow: hidden;
  background: #f8f9fa;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.dashboard-subtitle {
  color: #666;
  margin: 0;
}

.add-column-btn {
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: 500;
}

.add-column-btn:hover {
  background: #0056b3;
}

/* Kanban Board */
.kanban-board {
  display: flex;
  gap: 1.5rem;
  height: calc(100vh - 150px);
  overflow-x: auto;
  padding-bottom: 1rem;
}

.kanban-column {
  min-width: 300px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  max-height: 100%;
}

.column-header {
  padding: 1rem;
  border-bottom: 1px solid #e1e5e9;
  border-top: 3px solid #6c757d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.column-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.column-title {
  margin: 0;
  color: #333;
  font-size: 1rem;
}

.column-count {
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.column-points {
  color: #6c757d;
  font-size: 0.85rem;
}

.remove-column-btn {
  background: none;
  border: none;
  color: #dc3545;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
}

.remove-column-btn:hover {
  background: #f8d7da;
}

/* Issues Container */
.issues-container {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.issue-card {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.issue-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.issue-id {
  color: #0066cc;
  font-weight: 500;
  font-size: 0.85rem;
}

.issue-type {
  font-size: 1rem;
}

.issue-title {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 0.95rem;
  line-height: 1.4;
}

.issue-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.issue-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.priority-badge {
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.story-points {
  color: #6c757d;
  font-size: 0.8rem;
}

.assignee-avatar {
  width: 28px;
  height: 28px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
}

.add-issue-btn {
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 6px;
  padding: 1rem;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 0.5rem;
}

.add-issue-btn:hover {
  background: #e9ecef;
  border-color: #0066cc;
  color: #0066cc;
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  min-width: 300px;
}

.modal-content h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.column-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn-primary, .btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background: #0066cc;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

/* Issue Modal */
.issue-modal {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
}

.issue-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid #e1e5e9;
}

.issue-modal-header h2 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.issue-modal-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.issue-type-full {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.story-points-full {
  color: #6c757d;
  font-size: 0.9rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0.25rem;
}

.issue-modal-body {
  padding: 2rem;
}

.issue-field {
  margin-bottom: 1.5rem;
}

.issue-field label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 0.5rem;
}

.issue-field span {
  color: #666;
}

.issue-field p {
  color: #666;
  line-height: 1.6;
  margin: 0;
}
</style>