<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import AddIssueView from './AddIssueView.vue'
import CreateSprintView from './CreateSprintView.vue'
import axios from 'axios'

// Data
const bulkEditMode = ref(false)
const selectedIssues = ref([])
const viewMode = ref('list')
const selectedEpic = ref('')
const selectedAssignee = ref('')
const searchQuery = ref('')
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const showAddIssueModal = ref(false)
const showCreateSprintModal = ref(false)
const sprints = ref([])
const backlogIssues = ref([])
const isDragOver = ref(false)
const issueTypes = ref([])
const userCache = ref({})

// New drag state management
const dragState = ref({
  isDragging: false,
  draggedIssue: null,
  dragOverTarget: null
})

// Computed properties
const filteredBacklogIssues = computed(() => {
  let filtered = backlogIssues.value.filter(issue => !issue.sprint) 

  if (selectedEpic.value) {
    filtered = filtered.filter(issue => issue.epic?.id === parseInt(selectedEpic.value))
  }

  if (selectedAssignee.value) {
    filtered = filtered.filter(issue => issue.assignee?.id === parseInt(selectedAssignee.value))
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(issue => 
      issue.title.toLowerCase().includes(query) ||
      issue.key.toLowerCase().includes(query) ||
      (issue.description && issue.description.toLowerCase().includes(query))
    )
  }

  return filtered
})

const totalStoryPoints = computed(() => {
  return filteredBacklogIssues.value.reduce((total, issue) => total + (issue.storyPoints || 0), 0)
})

// Enhanced drag and drop methods
const onDragStart = (event, issue) => {
  dragState.value = {
    isDragging: true,
    draggedIssue: issue,
    dragOverTarget: null
  }
  
  // Set drag data
  event.dataTransfer.setData('text/plain', JSON.stringify(issue))
  event.dataTransfer.effectAllowed = 'move'
  
  // Add drag image styling
  const dragImage = event.target.cloneNode(true)
  dragImage.style.transform = 'rotate(5deg)'
  dragImage.style.opacity = '0.8'
  event.dataTransfer.setDragImage(dragImage, 0, 0)
}

const onDragEnd = () => {
  // Reset drag state
  dragState.value = {
    isDragging: false,
    draggedIssue: null,
    dragOverTarget: null
  }
}

const onDragEnter = (event, target) => {
  event.preventDefault()
  dragState.value.dragOverTarget = target
}

const onDragLeave = (event, target) => {
  // Only reset if we're actually leaving the target area
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    if (dragState.value.dragOverTarget === target) {
      dragState.value.dragOverTarget = null
    }
  }
}

const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const onDrop = async (event, target) => {
  event.preventDefault()
  
  const issueData = JSON.parse(event.dataTransfer.getData('text/plain'))
  
  try {
    const token = localStorage.getItem('token')
    const sprintId = target === 'backlog' ? null : target
    
    await axios.patch(`/api/issues/${issueData.id}/`, { 
      sprint: sprintId 
    }, {
      headers: { Authorization: `Token ${token}` }
    })
    
    // Show success feedback
    showDropSuccess(target, issueData)
    
    await fetchIssues()
  } catch (e) {
    console.error('Failed to move issue:', e)
    // Show error feedback
    showDropError()
  }
  
  // Reset drag state
  dragState.value = {
    isDragging: false,
    draggedIssue: null,
    dragOverTarget: null
  }
}

// Visual feedback methods
const showDropSuccess = (target, issue) => {
  // You can implement toast notifications or other feedback here
  console.log(`Successfully moved ${issue.key} to ${target === 'backlog' ? 'backlog' : `sprint ${target}`}`)
}

const showDropError = () => {
  console.error('Failed to move issue')
}

// Helper methods to check drag states
const isSprintDragTarget = (sprintId) => {
  return dragState.value.dragOverTarget === sprintId && dragState.value.isDragging
}

const isBacklogDragTarget = () => {
  return dragState.value.dragOverTarget === 'backlog' && dragState.value.isDragging
}

const isIssueDragging = (issueId) => {
  return dragState.value.isDragging && dragState.value.draggedIssue?.id === issueId
}

// Methods
const toggleBulkEdit = () => {
  bulkEditMode.value = !bulkEditMode.value
  if (!bulkEditMode.value) {
    selectedIssues.value = []
  }
}

const selectIssue = (issueId) => {
  if (bulkEditMode.value) {
    toggleIssueSelection(issueId)
  } else {
    // Navigate to issue detail or open modal
    console.log('Open issue:', issueId)
  }
}

const toggleIssueSelection = (issueId) => {
  const index = selectedIssues.value.indexOf(issueId)
  if (index > -1) {
    selectedIssues.value.splice(index, 1)
  } else {
    selectedIssues.value.push(issueId)
  }
}

const createIssue = () => {
  console.log('Create new issue')
}

const editSprint = (sprintId) => {
  console.log('Edit sprint:', sprintId)
}

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

const fetchSprints = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/sprints/`)
  sprints.value = res.data
}

const fetchIssues = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/`)
  backlogIssues.value = res.data
  console.log('Fetched issues:', backlogIssues.value)
}

const fetchIssueTypes = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get('/api/issue-types/')
  issueTypes.value = res.data
}

const startSprint = async (sprintId) => {
  // PATCH sprint status to 'active'
  const token = localStorage.getItem('token')
  await axios.patch(`/api/sprints/${sprintId}/`, { status: 'active' }, {
    headers: { Authorization: `Token ${token}` }
  })
  fetchSprints()
}

const getSprintIssues = (sprintId) => {
  return backlogIssues.value.filter(issue => issue.sprint === sprintId)
}

const onIssueCreated = (issueData) => {
  // Optionally refresh issues or show a toast
  showAddIssueModal.value = false
  fetchIssues()
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

const getAssigneeInitials = async (assigneeId) => {
  const user = await fetchUserShort(assigneeId)
  return user ? user.initials : ''
}

onMounted(() => {
  fetchSprints()
  fetchIssues().then(() => {
    filteredBacklogIssues.value.forEach(issue => {
      if (issue.assignee) fetchUserShort(issue.assignee)
    })
    sprints.value.forEach(sprint => {
      getSprintIssues(sprint.id).forEach(issue => {
        if (issue.assignee) fetchUserShort(issue.assignee)
      })
    })
  })
  fetchIssueTypes()
})

watch(currentProject, () => {
  fetchSprints()
  fetchIssues()
  fetchIssueTypes()
})
</script>

<template>
  <div class="backlog-view">
    <div class="page-header">
      <div class="header-content">
        <h1>Backlog</h1>
        <p class="page-description">Prioritize your work and plan future sprints</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="toggleBulkEdit">
          {{ bulkEditMode ? 'Cancel' : 'Bulk Edit' }}
        </button>
        <button class="btn btn-primary" @click="showAddIssueModal = true">
          + Create Issue
        </button>
        <button class="btn btn-primary" @click="showCreateSprintModal = true">
          + Create Sprint
        </button>
      </div>
    </div>

    <div class="backlog-filters">
      <div class="filter-group">
        <input 
          type="text" 
          v-model="searchQuery"
          placeholder="Search issues..."
          class="search-input"
        />
      </div>
      
      <div class="view-options">
        <button 
          class="view-btn" 
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          📋 List
        </button>
        <button 
          class="view-btn" 
          :class="{ active: viewMode === 'detailed' }"
          @click="viewMode = 'detailed'"
        >
          📄 Detailed
        </button>
      </div>
    </div>

    <div class="backlog-content">
      <!-- Sprint Planning Section -->
      <div class="sprint-planning" v-if="sprints.length > 0">
        <h3>Sprint Planning</h3>
        <div 
          v-for="sprint in sprints" 
          :key="sprint.id"
          class="sprint-container"
          :class="{ 
            'drag-over': isSprintDragTarget(sprint.id),
            'drag-active': dragState.isDragging
          }"
          @drop="onDrop($event, sprint.id)"
          @dragover="onDragOver"
          @dragenter="onDragEnter($event, sprint.id)"
          @dragleave="onDragLeave($event, sprint.id)"
        >
          <div class="sprint-header">
            <div class="sprint-info">
              <span class="sprint-name">{{ sprint.name }}</span>
              <span class="sprint-dates">{{ sprint.startDate }} - {{ sprint.endDate }}</span>
              <span class="sprint-capacity">{{ getSprintIssues(sprint.id).length }} issues</span>
            </div>
            <div class="sprint-actions">
              <button class="btn-icon" @click="startSprint(sprint.id)">▶️ Start Sprint</button>
              <button class="btn-icon" @click="editSprint(sprint.id)">✏️</button>
            </div>
          </div>
          
          <div class="sprint-issues" :class="{ empty: getSprintIssues(sprint.id).length === 0 }">
            <div 
              v-for="issue in getSprintIssues(sprint.id)" 
              :key="issue.id"
              class="issue-card"
              :class="{ 
                selected: selectedIssues.includes(issue.id),
                dragging: isIssueDragging(issue.id)
              }"
              draggable="true"
              @dragstart="onDragStart($event, issue)"
              @dragend="onDragEnd"
              @click="selectIssue(issue.id)"
            >
              <div class="issue-header">
                <span class="issue-key">{{ issue.key }}</span>
                <span class="issue-type">{{ getIssueTypeIcon(issue.issue_type) }}</span>
                <span class="issue-priority">{{ getPriorityIcon(issue.priority) }}</span>
              </div>
              <div class="issue-title">{{ issue.title }}</div>
              <div class="issue-meta">
                <span class="issue-assignee" v-if="issue.assignee">
                  {{ userCache[issue.assignee]?.initials || '' }}
                </span>
                <span class="issue-story-points" v-if="issue.storyPoints">
                  {{ issue.storyPoints }}
                </span>
              </div>
            </div>
            
            <div 
              v-if="getSprintIssues(sprint.id).length === 0" 
              class="empty-sprint"
              :class="{ 'drag-target-active': isSprintDragTarget(sprint.id) }"
            >
              <div class="empty-sprint-content">
                <div class="empty-icon">📋</div>
                <div class="empty-text">
                  {{ isSprintDragTarget(sprint.id) ? 'Drop issue here' : `Drop issues here to add to ${sprint.name}` }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- Drop zone indicator -->
          <div v-if="isSprintDragTarget(sprint.id)" class="drop-zone-indicator">
            <div class="drop-zone-content">
              <span class="drop-icon">⬇️</span>
              <span>Drop to add to {{ sprint.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Product Backlog -->
      <div 
        class="product-backlog"
        :class="{ 
          'drag-over': isBacklogDragTarget(),
          'drag-active': dragState.isDragging
        }"
        @drop="onDrop($event, 'backlog')"
        @dragover="onDragOver"
        @dragenter="onDragEnter($event, 'backlog')"
        @dragleave="onDragLeave($event, 'backlog')"
      >
        <div class="backlog-header">
          <h3>Product Backlog</h3>
          <div class="backlog-stats">
            <span>{{ filteredBacklogIssues.length }} issues</span>
            <span>{{ totalStoryPoints }} story points</span>
          </div>
        </div>

        <div class="backlog-issues">
          <div 
            v-for="issue in filteredBacklogIssues" 
            :key="issue.id"
            class="issue-card"
            :class="{ 
              selected: selectedIssues.includes(issue.id),
              detailed: viewMode === 'detailed',
              dragging: isIssueDragging(issue.id)
            }"
            draggable="true"
            @dragstart="onDragStart($event, issue)"
            @dragend="onDragEnd"
            @click="selectIssue(issue.id)"
          >
            <input 
              v-if="bulkEditMode"
              type="checkbox"
              :checked="selectedIssues.includes(issue.id)"
              @click.stop="toggleIssueSelection(issue.id)"
              class="issue-checkbox"
            />
            
            <div class="issue-content">
              <div class="issue-header">
                <span class="issue-key">{{ issue.key }}</span>
                <span class="issue-type">{{ getIssueTypeIcon(issue.issue_type) }}</span>
                <span class="issue-priority">{{ getPriorityIcon(issue.priority) }}</span>
              </div>
              
              <div class="issue-title">{{ issue.title }}</div>
              
              <div class="issue-description" v-if="viewMode === 'detailed' && issue.description">
                {{ issue.description }}
              </div>
              
              <div class="issue-meta">
                <span class="issue-epic" v-if="issue.epic">
                  📚 {{ issue.epic.name }}
                </span>
                <span class="issue-assignee" v-if="issue.assignee">
                  {{ userCache[issue.assignee]?.initials || '' }}
                </span>
                <span class="issue-story-points" v-if="issue.storyPoints">
                  {{ issue.storyPoints }} SP
                </span>
                <span class="issue-status">{{ issue.status }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Backlog drop zone indicator -->
        <div v-if="isBacklogDragTarget()" class="drop-zone-indicator backlog-drop">
          <div class="drop-zone-content">
            <span class="drop-icon">📋</span>
            <span>Drop to return to backlog</span>
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
  <CreateSprintView
    :showModal="showCreateSprintModal"
    @close="showCreateSprintModal = false"
    @save="fetchSprints"
  />
</template>

<style scoped>
.backlog-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn {
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

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 3px;
  transition: background-color 0.2s;
}

.btn-icon:hover {
  background: #f8f9fa;
}

.sprint-issues.drag-over {
  border-color: #0066cc;
  background: #e6f2ff;
}
.backlog-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
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

.filter-select, .search-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  outline: none;
}

.filter-select:focus, .search-input:focus {
  border-color: #0066cc;
}

.search-input {
  width: 250px;
}

.view-options {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn:hover {
  background: #e9ecef;
}

.view-btn.active {
  background: #0066cc;
  color: white;
  border-color: #0066cc;
}

.backlog-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.sprint-planning h3, .backlog-header h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.sprint-container {
  background: white;
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sprint-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e1e5e9;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.sprint-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sprint-name {
  font-weight: bold;
  color: #333;
}

.sprint-dates {
  color: #666;
  font-size: 0.9rem;
}

.sprint-capacity {
  color: #0066cc;
  font-size: 0.9rem;
  font-weight: 500;
}

.sprint-actions {
  display: flex;
  gap: 0.5rem;
}

.sprint-issues {
  padding: 1rem;
  min-height: 60px;
  border: 2px dashed transparent;
  transition: border-color 0.2s;
}

.sprint-issues.empty {
  border-color: #ddd;
}

.empty-sprint {
  text-align: center;
  color: #999;
  padding: 2rem;
  font-style: italic;
}

.product-backlog {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex: 1;
}

.backlog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.backlog-stats {
  display: flex;
  gap: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.backlog-issues {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.issue-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.issue-card:hover {
  border-color: #0066cc;
  box-shadow: 0 2px 4px rgba(0, 102, 204, 0.1);
}

.issue-card.selected {
  border-color: #0066cc;
  background: #f0f8ff;
}

.issue-card.detailed {
  flex-direction: column;
  align-items: flex-start;
}

.issue-checkbox {
  margin-right: 0.5rem;
}

.issue-content {
  flex: 1;
  width: 100%;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.issue-key {
  background: #f8f9fa;
  color: #0066cc;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: bold;
}

.issue-type, .issue-priority {
  font-size: 1rem;
}

.issue-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.5rem;
}

.issue-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.issue-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.issue-epic {
  color: #8b5cf6;
  font-size: 0.8rem;
}

.issue-assignee {
  background: #0066cc;
  color: white;
  border-radius: 50%;
  font-size: 0.9rem;
  font-weight: bold;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-transform: uppercase;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.issue-story-points {
  background: #28a745;
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: bold;
}

.issue-status {
  color: #666;
  background: #f8f9fa;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .backlog-filters {
    flex-direction: column;
    gap: 1rem;
  }
  
  .filter-group {
    flex-wrap: wrap;
  }
  
  .search-input {
    width: 200px;
  }
  
  .issue-meta {
    flex-wrap: wrap;
  }
}

@media (prefers-color-scheme: dark) {
  .backlog-view,
  .product-backlog,
  .sprint-container,
  .backlog-filters,
  .issue-card,
  .sprint-header,
  .empty-sprint {
    background: #181a1b !important;
    color: #f3f3f3 !important;
    border-color: #333 !important;
  }
  .page-header,
  .header-content h1,
  .page-description,
  .backlog-header h3,
  .sprint-name,
  .sprint-dates,
  .sprint-capacity,
  .issue-title,
  .issue-description,
  .issue-meta,
  .issue-key,
  .issue-type,
  .issue-priority,
  .issue-status,
  .issue-epic,
  .issue-assignee,
  .issue-story-points,
  .backlog-stats,
  .filter-select,
  .search-input,
  .view-btn,
  .btn,
  .btn-primary,
  .btn-secondary,
  .btn-icon {
    color: #f3f3f3 !important;
    background: #232526 !important;
    border-color: #444 !important;
  }
  .btn-primary {
    background: #0056b3 !important;
    color: #fff !important;
  }
  .btn-secondary {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border: 1px solid #444 !important;
  }
  .view-btn.active {
    background: #0056b3 !important;
    color: #fff !important;
    border-color: #0056b3 !important;
  }
  .issue-card.selected {
    background: #232526 !important;
    border-color: #0056b3 !important;
  }
  .issue-assignee {
    background: #0056b3 !important;
    color: #fff !important;
  }
  .issue-story-points {
    background: #28a745 !important;
    color: #fff !important;
  }
  .issue-key {
    background: #232526 !important;
    color: #4ea1ff !important;
  }
  .issue-status {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }
  .empty-sprint {
    color: #aaa !important;
  }
}
</style>