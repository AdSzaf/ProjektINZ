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

const showIssueModal = ref(false)
const selectedIssue = ref(null)
const showEditIssueModal = ref(false)
const editIssueData = ref(null)

const showEditSprintModal = ref(false)
const editSprintData = ref(null)

// New drag state management
const dragState = ref({
  isDragging: false,
  draggedIssue: null,
  dragOverTarget: null
})

// Computed properties
const filteredBacklogIssues = computed(() => {
  // Build map for sprint status lookups
  const sprintById = new Map(sprints.value.map(s => [s.id, s]))
  // Include:
  // - issues with no sprint
  // - issues whose sprint is completed AND issue is not done
  let filtered = backlogIssues.value.filter(issue => {
    if (!issue.sprint) return true
    const sprint = sprintById.get(issue.sprint)
    const isDone = String(issue.status || '').toLowerCase() === 'done'
    return sprint && sprint.status === 'completed' && !isDone
  }) 

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

// Sprints that can be planned into (exclude completed)
const plannableSprints = computed(() => {
  return sprints.value.filter(s => s.status !== 'completed')
})

// Helpers
const getSprintById = (sid) => sprints.value.find(s => s.id === sid)
const isIssueFromCompletedSprint = (issue) => {
  if (!issue.sprint) return false
  const s = getSprintById(issue.sprint)
  const isDone = String(issue.status || '').toLowerCase() === 'done'
  return !!s && s.status === 'completed' && !isDone
}

const reassignIssueSprint = async (issueId, newSprintId) => {
  try {
    const token = localStorage.getItem('token')
    await axios.patch(`/api/issues/${issueId}/`, {
      sprint: newSprintId || null
    }, {
      headers: { Authorization: `Token ${token}` }
    })
    await fetchIssues()
  } catch (e) {
    console.error('Failed to reassign sprint:', e)
  }
}

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

const toggleIssueSelection = (issueId) => {
  const index = selectedIssues.value.indexOf(issueId)
  if (index > -1) {
    selectedIssues.value.splice(index, 1)
  } else {
    selectedIssues.value.push(issueId)
  }
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

const createIssue = () => {
  console.log('Create new issue')
}

const editSprint = (sprintId) => {
  const sprint = sprints.value.find(s => s.id === sprintId)
  editSprintData.value = sprint
  showEditSprintModal.value = true
}

const closeEditSprintModal = () => {
  showEditSprintModal.value = false
  editSprintData.value = null
}

const onSprintEdited = () => {
  closeEditSprintModal()
  fetchSprints()
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

const getSprintProgress = (sprintId) => {
  const sprintIssues = getSprintIssues(sprintId)
  if (!sprintIssues.length) return 0
  const doneCount = sprintIssues.filter(i => i.status === 'done' || i.status === 'Done').length
  return Math.round((doneCount / sprintIssues.length) * 100)
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

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return dateStr.split('T')[0]
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
      <div class="sprint-planning" v-if="plannableSprints.length > 0">
        <h3>Sprint Planning</h3>
        <div 
          v-for="sprint in plannableSprints" 
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
              <span class="sprint-dates">{{ formatDate(sprint.start_date) }} - {{ formatDate(sprint.end_date) }}</span>
              <span class="sprint-capacity">{{ getSprintIssues(sprint.id).length }} issues</span>
              <span class="sprint-status" :class="`status-${sprint.status}`">
                {{ sprint.status === 'active' ? 'Active' : sprint.status === 'completed' ? 'Completed' : 'Planned' }}
              </span>
              <span class="sprint-end-date" v-if="sprint.status === 'active'">
                Ends: {{ formatDate(sprint.end_date) }}
              </span>
              <div class="sprint-progress-bar">
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    :style="{ width: `${getSprintProgress(sprint.id)}%` }"
                  ></div>
                </div>
                <span class="progress-text">{{ getSprintProgress(sprint.id) }}%</span>
              </div>
            </div>
            <div class="sprint-actions">
              <button 
                class="btn-icon" 
                v-if="sprint.status === 'future'" 
                @click="startSprint(sprint.id)">
                ▶️ Start Sprint
              </button>
              <button 
                class="btn-icon" 
                v-if="sprint.status === 'active'" 
                disabled>
                ✅ Sprint Active
              </button>
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
              @click="openIssueDetails(issue)"
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
            @click="openIssueDetails(issue)"
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
                <span v-if="isIssueFromCompletedSprint(issue)" class="origin-sprint-tag">
                  🏁 From {{ getSprintById(issue.sprint)?.name }}
                </span>
              </div>
              <div v-if="isIssueFromCompletedSprint(issue)" class="reassign-row">
                <label class="reassign-label">Reassign to sprint:</label>
                <select class="reassign-select" @click.stop @change="reassignIssueSprint(issue.id, $event.target.value || null)">
                  <option value="">Backlog</option>
                  <option v-for="sp in plannableSprints" :key="sp.id" :value="sp.id">
                    {{ sp.name }}
                  </option>
                </select>
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

        <!-- Issue Details Modal -->
        <div v-if="showIssueModal" class="modal-overlay" @click="closeIssueModal">
          <div class="issue-modal" @click.stop>
            <div class="issue-modal-header">
              <div>
                <h2>{{ selectedIssue?.key }}: {{ selectedIssue?.title }}</h2>
                <div class="issue-modal-meta">
                  <span class="issue-type-full">
                    {{ getIssueTypeIcon(selectedIssue?.issue_type) }}
                    {{ issueTypes.find(t => t.id === String(selectedIssue?.issue_type))?.name || '' }}
                  </span>
                  <span class="issue-priority">{{ getPriorityIcon(selectedIssue?.priority) }}</span>
                  <span class="story-points-full">{{ selectedIssue?.story_points ?? selectedIssue?.storyPoints ?? 0 }} Story Points</span>
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
                <span>{{ userCache[selectedIssue?.assignee]?.initials || 'Unassigned' }}</span>
              </div>
              <div class="issue-field">
                <label>Status:</label>
                <span>{{ selectedIssue?.status }}</span>
              </div>
              <div class="issue-field">
                <label>Description:</label>
                <p>{{ selectedIssue?.description || 'No description provided.' }}</p>
              </div>
            </div>
          </div>
        </div>
        <AddIssueView
        :showModal="showEditIssueModal"
        mode="edit"
        :issue="editIssueData"
        @close="closeEditIssueModal"
        @save="onIssueEdited"
      />
      <CreateSprintView
      :showModal="showEditSprintModal"
      mode="edit"
      :sprint="editSprintData"
      @close="closeEditSprintModal"
      @save="onSprintEdited"
    />
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

.sprint-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start; /* Changed from center to flex-start */
  padding: 1rem;
  border-bottom: 1px solid #e1e5e9;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.sprint-info {
  display: flex;
  flex-direction: column; /* Changed to column layout */
  gap: 0.5rem; /* Reduced gap for tighter spacing */
  flex: 1; /* Take available space */
  min-width: 0; /* Allow shrinking */
}

/* If you can't modify template, use this instead */
.sprint-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 0;
}

/* Create a virtual row by styling direct children */
.sprint-info > span:not(.progress-text) {
  display: inline-block;
  margin-right: 1rem;
}

/* Force progress bar to be on its own line */
.sprint-info > .sprint-progress-bar {
  display: block;
  width: 100%;
}

.sprint-name {
  font-weight: bold;
  color: #333;
  white-space: nowrap; /* Prevent text wrapping */
}

.sprint-dates {
  color: #666;
  font-size: 0.9rem;
  white-space: nowrap;
}

.sprint-capacity {
  color: #0066cc;
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
}

.sprint-status {
  font-size: 0.85rem;
  font-weight: bold;
  padding: 0.2rem 0.5rem; /* Add padding for better visual separation */
  border-radius: 3px; /* Add border radius */
  white-space: nowrap;
}

.sprint-status.status-active {
  color: #28a745;
  background: #d4edda;
}

.sprint-status.status-completed {
  color: #888;
  background: #f8f9fa;
}

.sprint-status.status-planned {
  color: #0066cc;
  background: #e6f2ff;
}

.sprint-end-date {
  font-size: 0.85rem;
  color: #666;
  white-space: nowrap;
}

/* Progress bar should be full width and separate */
.sprint-progress-bar {
  width: 100%; /* Full width */
  margin-top: 0.5rem; /* Space from metadata row */
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #e1e5e9;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.25rem;
  border: 1px solid #ddd;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: #0066cc;
  transition: width 0.3s;
  min-width: 2px;
  display: block;
}


.progress-text {
  font-size: 0.8rem;
  color: #0066cc;
  font-weight: bold;
}

.sprint-actions {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start; /* Align to top */
  flex-shrink: 0; /* Don't shrink */
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

  .sprint-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .sprint-info > .sprint-meta-row {
    gap: 0.5rem;
  }
  
  .sprint-actions {
    align-self: stretch;
    justify-content: flex-end;
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
  .sprint-progress-bar,
  .progress-text,
  .sprint-status,
  .sprint-end-date,
  .sprint-status.status-active,
  .sprint-status.status-completed,
  .sprint-status.status-planned,
  .modal-content,
  .column-input,
  .modal-actions,
  .btn-primary,
  .btn-secondary,
  .issue-modal,
  .issue-modal-header,
  .issue-modal-meta,
  .issue-type-full,
  .story-points-full,
  .close-btn,
  .issue-modal-body,
  .issue-field,
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
  .progress-bar {
    background: #232526 !important;
    border-color: #444 !important;
  }
  .progress-fill {
    background: #4ea1ff !important;
  }
  .btn-edit {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }
  .btn-edit:hover {
    background: #0056b3 !important;
    color: #fff !important;
    border-color: #0056b3 !important;
  }
}
</style>