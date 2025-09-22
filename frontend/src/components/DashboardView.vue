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
const epics = ref([])
const sprints = ref([])
const issueTypes = ref([])
const showDeleteColumnModal = ref(false)
const columnToDelete = ref(null)
const userCache = ref({})
const showEditIssueModal = ref(false)
const editIssueData = ref(null)
const availableTags = ref([])
const selectedTagIds = ref([])
const showTagFilter = ref(false)

const fetchIssues = async () => {
  if (!currentProject.value?.id) {
    issues.value = []
    return
  }
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/`)
  issues.value = res.data
  issues.value.forEach(issue => {
    if (issue.assignee) fetchUserShort(issue.assignee)
  })
  console.log('Fetched issues:', issues.value)
}

const fetchTags = async () => {
  if (!currentProject.value?.id) {
    availableTags.value = []
    return
  }
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/tags/`)
  availableTags.value = res.data
}

const confirmDeleteColumn = (column) => {
  columnToDelete.value = column
  showDeleteColumnModal.value = true
}

const cancelDeleteColumn = () => {
  showDeleteColumnModal.value = false
  columnToDelete.value = null
}

// UI state
const showAddColumn = ref(false)
const newColumnName = ref('')
const draggedIssue = ref(null)
const showIssueModal = ref(false)
const selectedIssue = ref(null)

// Filters
const currentUserId = ref('')
const currentUserEmail = ref('')
const selectedSprint = ref('all')
const assignmentOrType = ref('all') // 'all' | 'unassigned' | 'assigned_me' | `type:${typeId}`

const sprintOptions = computed(() => {
  const opts = [{ value: 'all', label: 'All sprints' }]
  const sorted = [...sprints.value].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
  sorted.forEach(s => opts.push({ value: String(s.id), label: s.name }))
  return opts
})

const assignmentTypeOptions = computed(() => {
  const base = [
    { value: 'all', label: 'All issues' },
    { value: 'unassigned', label: 'Unassigned issues' },
    { value: 'assigned_me', label: 'Assigned to me' },
  ]
  const types = [...issueTypes.value]
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    .map(t => ({ value: `type:${String(t.id)}`, label: `Type: ${t.name}` }))
  return [...base, ...types]
})

// Computed properties
const statusMap = {
  to_do: 'todo',
  in_progress: 'inprogress',
  done: 'done'
}

const filteredIssues = computed(() => {
  return issues.value.filter(issue => {
    // Sprint filter
    if (selectedSprint.value !== 'all') {
      if (!issue.sprint || String(issue.sprint) !== String(selectedSprint.value)) {
        return false
      }
    }
    
    // Assignment/type filter
    if (assignmentOrType.value === 'unassigned') {
      if (issue.assignee) return false
    } else if (assignmentOrType.value === 'assigned_me') {
      if (!currentUserId.value) return false
      if (String(issue.assignee) !== String(currentUserId.value)) return false
    } else if (assignmentOrType.value.startsWith('type:')) {
      const typeId = assignmentOrType.value.split(':')[1]
      if (String(issue.issue_type) !== String(typeId)) return false
    }
    
    // Tag filter
    if (selectedTagIds.value.length > 0) {
      const issueTagIds = (issue.tags || []).map(tag => tag.id)
      const hasMatchingTag = selectedTagIds.value.some(selectedTagId => 
        issueTagIds.includes(selectedTagId)
      )
      if (!hasMatchingTag) return false
    }
    
    return true
  })
})

const tagFilterOptions = computed(() => {
  const base = [{ value: 'all', label: 'All tags' }]
  const tagOpts = availableTags.value.map(tag => ({
    value: tag.id,
    label: tag.name,
    color: tag.color
  }))
  return [...base, ...tagOpts]
})

const getIssuesByStatus = (category) => {
  return filteredIssues.value.filter(issue => issue.status === category)
}

const getTotalPoints = (status) => {
  return getIssuesByStatus(status).reduce((total, issue) => total + (issue.story_points ?? 0), 0)
}

const reverseStatusMap = {
  todo: 'to_do',
  inprogress: 'in_progress',
  done: 'done'
}

const fetchIssueTypes = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get('/api/issue-types/')
  issueTypes.value = res.data
  console.log('Fetched issue types:', issueTypes.value) 
}

const fetchSprintsList = async () => {
  if (!currentProject.value?.id) {
    sprints.value = []
    return
  }
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/sprints/`)
  sprints.value = res.data
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

const deleteColumn = async () => {
  if (!columnToDelete.value) return
  const token = localStorage.getItem('token')
  try {
    await axios.delete(`/api/projects/${currentProject.value.id}/workflow-statuses/${columnToDelete.value.category}/`)
    // Optionally, refresh columns and issues
    fetchColumns()
    fetchIssues()
  } catch (e) {
    console.error('Failed to delete column:', e)
  }
  showDeleteColumnModal.value = false
  columnToDelete.value = null
}

const openIssueDetails = (issue) => {
  selectedIssue.value = issue
  showIssueModal.value = true
}

const closeIssueModal = () => {
  showIssueModal.value = false
  selectedIssue.value = null
}

const startEditIssue = (issue) => {
  editIssueData.value = issue
  showEditIssueModal.value = true
}
const closeEditIssueModal = () => {
  showEditIssueModal.value = false
  editIssueData.value = null
}
const onIssueEdited = () => {
  closeEditIssueModal()
  fetchIssues()
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

const getTypeIconById = (typeId) => {
  const type = issueTypes.value.find(t => t.id === String(typeId))
  return type ? type.icon : '📄'
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
  // Try to resolve currentUserId via email if not set
  if (!currentUserId.value && currentUserEmail.value) {
    const me = users.value.find(u => u.email === currentUserEmail.value)
    if (me) currentUserId.value = me.id
  }
}

const fetchUserShort = async (userId) => {
  if (!userId) return null
  if (userCache.value[userId]) return userCache.value[userId]
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/users/${userId}/short/`)
  userCache.value[userId] = res.data
  return res.data
}

onMounted(() => {
  fetchColumns()
  fetchIssues()
  fetchUsers()
  fetchIssueTypes()
  fetchSprintsList()
  fetchTags()
  // current user id
  const token = localStorage.getItem('token')
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    axios.get('/api/me/').then(r => {
      // /api/me does not include id in serializer; use email
      currentUserId.value = r.data.id || ''
      currentUserEmail.value = r.data.email || ''
      // If users list loaded, map email -> id
      if (!currentUserId.value && users.value.length) {
        const me = users.value.find(u => u.email === currentUserEmail.value)
        if (me) currentUserId.value = me.id
      }
    }).catch(() => {})
  }
})
watch(currentProject, () => {
  fetchColumns()
  fetchIssues()
  fetchUsers()
  fetchIssueTypes()
  fetchSprintsList()
  fetchTags()
})
</script>

<template>
  <div v-if="!currentProject" class="no-projects-message">
    <h2>No projects found</h2>
    <p>Create your first project to get started!</p>
    <button class="btn btn-primary" @click="$router.push('/create-project')">+ Create Project</button>
  </div>
  <div v-else class="dashboard-container">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1>Sprint Board</h1>
        <p class="dashboard-subtitle">Drag and drop issues to update their status</p>
        <div class="filters-row">
          <select v-model="selectedSprint" class="filter-select">
            <option v-for="opt in sprintOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <select v-model="assignmentOrType" class="filter-select">
            <option v-for="opt in assignmentTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <div class="tag-filter-container">
            <div class="tag-filter-dropdown">
              <button 
                class="tag-filter-btn" 
                @click="showTagFilter = !showTagFilter"
                :class="{ active: selectedTagIds.length > 0 }"
              >
                Tags {{ selectedTagIds.length > 0 ? `(${selectedTagIds.length})` : '' }}
                <span class="dropdown-arrow">▼</span>
              </button>
              
              <div v-if="showTagFilter" class="tag-filter-options">
                <div class="tag-filter-header">
                  <span>Filter by tags</span>
                  <button 
                    v-if="selectedTagIds.length > 0" 
                    @click="selectedTagIds = []"
                    class="clear-tags-btn"
                  >
                    Clear all
                  </button>
                </div>
                <div class="tag-options-list">
                  <label 
                    v-for="tag in availableTags" 
                    :key="tag.id"
                    class="tag-option-item"
                  >
                    <input 
                      type="checkbox" 
                      :value="tag.id"
                      v-model="selectedTagIds"
                      class="tag-checkbox"
                    />
                    <div class="tag-preview">
                      <div 
                        class="tag-color-dot" 
                        :style="{ backgroundColor: tag.color }"
                      ></div>
                      <span>{{ tag.name }}</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
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
            @click="confirmDeleteColumn(column)"
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
              <span class="issue-type">{{ getTypeIconById(issue.issue_type) }}</span>
            </div>

            <!-- Issue Title -->
            <h4 class="issue-title">{{ issue.title }}</h4>
            
            <!-- Add tags display before issue-footer -->
            <div v-if="issue.tags && issue.tags.length > 0" class="issue-tags">
              <div 
                v-for="tag in issue.tags.slice(0, 2)" 
                :key="tag.id"
                class="issue-tag"
                :style="{ backgroundColor: tag.color }"
              >
                {{ tag.name }}
              </div>
              <div v-if="issue.tags.length > 2" class="more-tags">
                +{{ issue.tags.length - 2 }}
              </div>
            </div>

            <!-- Issue Footer -->
            <div class="issue-footer">
              <div class="issue-meta">
                <span 
                  class="priority-badge" 
                  :style="{ backgroundColor: getPriorityColor(issue.priority) }"
                >
                  {{ issue.priority }}
                </span>
                <span class="story-points">{{ issue.story_points ?? 0 }} pts</span>
              </div>
              
              <div class="assignee-avatar" :title="getAssigneeName(issue.assignee)">
                {{ userCache[issue.assignee]?.initials || '' }}
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
              <span class="issue-type-full">
                {{ getTypeIconById(selectedIssue?.issue_type) }} 
                {{ issueTypes.find(t => t.id === String(selectedIssue?.issue_type))?.name || '' }}
              </span>
              <span 
                class="priority-badge" 
                :style="{ backgroundColor: getPriorityColor(selectedIssue?.priority) }"
              >
                {{ selectedIssue?.priority }}
              </span>
              <span class="story-points-full">{{ selectedIssue?.story_points ?? 0 }} Story Points</span>
            </div>
          </div>
          <div class="issue-modal-actions">
            <button class="btn-edit" @click="startEditIssue(selectedIssue)">✏️ Edit Issue</button>
            <button class="close-btn" @click="closeIssueModal">×</button>
          </div>
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
            <p>{{ selectedIssue?.description || 'No description provided.' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Column Confirmation Modal -->
    <div v-if="showDeleteColumnModal" class="modal-overlay" @click="cancelDeleteColumn">
      <div class="modal-content" @click.stop>
        <h3>Delete Column</h3>
        <p>
          Are you sure you want to delete the column "<b>{{ columnToDelete?.name }}</b>"?<br>
          <span style="color: #dc3545;">
            All issues in this column will be deleted!
          </span>
        </p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelDeleteColumn">Cancel</button>
          <button class="btn-primary" style="background:#dc3545;" @click="deleteColumn">Delete</button>
        </div>
      </div>
    </div>
  </div>
  <AddIssueView
  :showModal="showAddIssueModal"
  @close="showAddIssueModal = false"
  @save="onIssueCreated"
/>
<AddIssueView
  :showModal="showEditIssueModal"
  mode="edit"
  :issue="editIssueData"
  @close="closeEditIssueModal"
  @save="onIssueEdited"
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

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dashboard-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.dashboard-subtitle {
  color: #666;
  margin: 0;
}

.filters-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.filter-select {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #333;
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

.issue-modal-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-edit {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  padding: 0.4rem 0.8rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.btn-edit:hover {
  background: #e9ecef;
  color: #0066cc;
  border-color: #0066cc;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #f8f9fa;
}

.tag-filter-container {
  position: relative;
}

.tag-filter-dropdown {
  position: relative;
}

.tag-filter-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  font-size: 0.9rem;
}

.tag-filter-btn.active {
  border-color: #0066cc;
  color: #0066cc;
}

.dropdown-arrow {
  font-size: 0.7rem;
  transition: transform 0.2s;
}

.tag-filter-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  min-width: 250px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-height: 300px;
  overflow-y: auto;
}

.tag-filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 500;
}

.clear-tags-btn {
  background: none;
  border: none;
  color: #0066cc;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.25rem;
}

.clear-tags-btn:hover {
  text-decoration: underline;
}

.tag-options-list {
  padding: 0.5rem;
}

.tag-option-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.tag-option-item:hover {
  background: #f8f9fa;
}

.tag-checkbox {
  margin: 0;
}

.tag-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tag-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.issue-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.issue-tag {
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 500;
}

.more-tags {
  color: #6c757d;
  font-size: 0.7rem;
  padding: 0.2rem 0.4rem;
}

@media (prefers-color-scheme: dark) {
  .dashboard-container {
    background: #181a1b !important;
    color: #f3f3f3 !important;
  }
  .filter-select {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }
  
  .dashboard-header h1,
  .dashboard-subtitle {
    color: #f3f3f3 !important;
  }
  
  .add-column-btn {
    background: #0056b3 !important;
    color: #fff !important;
  }
  
  .add-column-btn:hover {
    background: #004494 !important;
  }
  
  .kanban-column {
    background: #232526 !important;
    border-color: #444 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
  }
  
  .column-header {
    background: #232526 !important;
    border-bottom-color: #444 !important;
    border-top-color: #666 !important;
  }
  
  .column-title {
    color: #f3f3f3 !important;
  }
  
  .column-count {
    background: #444 !important;
    color: #f3f3f3 !important;
  }
  
  .column-points {
    color: #aaa !important;
  }
  
  .remove-column-btn {
    color: #ff6b6b !important;
  }
  
  .remove-column-btn:hover {
    background: #4a1f1f !important;
  }
  
  .issues-container {
    background: #232526 !important;
  }
  
  .issue-card {
    background: #2c2f30 !important;
    border-color: #444 !important;
    color: #f3f3f3 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
  }
  
  .issue-card:hover {
    background: #353838 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
  }
  
  .issue-id {
    color: #4ea1ff !important;
  }
  
  .issue-title {
    color: #f3f3f3 !important;
  }
  
  .story-points {
    color: #aaa !important;
  }
  
  .assignee-avatar {
    background: #0056b3 !important;
    color: #fff !important;
  }
  
  .add-issue-btn {
    background: #2c2f30 !important;
    border-color: #444 !important;
    color: #aaa !important;
  }
  
  .add-issue-btn:hover {
    background: #353838 !important;
    border-color: #0056b3 !important;
    color: #4ea1ff !important;
  }
  
  .modal-overlay {
    background: rgba(0, 0, 0, 0.7) !important;
  }
  
  .modal-content {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }
  
  .modal-content h3 {
    color: #f3f3f3 !important;
  }
  
  .column-input {
    background: #2c2f30 !important;
    border-color: #444 !important;
    color: #f3f3f3 !important;
  }
  
  .btn-primary {
    background: #0056b3 !important;
    color: #fff !important;
  }
  
  .btn-secondary {
    background: #444 !important;
    color: #f3f3f3 !important;
  }
  
  .issue-modal {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }
  
  .issue-modal-header {
    background: #232526 !important;
    border-bottom-color: #444 !important;
  }
  
  .issue-modal-header h2 {
    color: #f3f3f3 !important;
  }
  
  .story-points-full {
    color: #aaa !important;
  }
  
  .close-btn {
    color: #aaa !important;
  }
  
  .close-btn:hover {
    background: #2c2f30 !important;
    color: #f3f3f3 !important;
  }
  
  .issue-modal-body {
    background: #232526 !important;
  }
  
  .issue-field label {
    color: #f3f3f3 !important;
  }
  
  .issue-field span,
  .issue-field p {
    color: #ccc !important;
  }
  
  .btn-edit {
    background: #2c2f30 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }
  
  .btn-edit:hover {
    background: #0056b3 !important;
    color: #fff !important;
    border-color: #0056b3 !important;
  }

  .tag-filter-btn {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .tag-filter-btn.active {
    border-color: #4ea1ff !important;
    color: #4ea1ff !important;
  }

  .tag-filter-options {
    background: #232526 !important;
    border-color: #444 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  }

  .tag-filter-header {
    border-bottom-color: #444 !important;
    color: #f3f3f3 !important;
  }

  .clear-tags-btn {
    color: #4ea1ff !important;
  }

  .tag-option-item {
    color: #f3f3f3 !important;
  }

  .tag-option-item:hover {
    background: #2a2d2e !important;
  }
}
</style>