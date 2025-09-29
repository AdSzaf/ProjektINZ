<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import AddIssueView from './AddIssueView.vue'
import axios from 'axios'
import IssueComments from './IssueComments.vue'

// Data
const showFilters = ref(false)
const showCreateModal = ref(false)
const selectedIssueDetails = ref(null)
const selectedIssues = ref([])
const bulkAction = ref('')
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const availableTags = ref([])
const showTagFilter = ref(false)

// Pagination
const currentPage = ref(1)
const pageSize = ref(25)

// Sorting
const sortField = ref('created')
const sortDirection = ref('desc')

// Team members (fetched from backend)
const teamMembers = ref([])

// Issues fetched from backend
const totalIssues = ref([])

// Caches for lookups
const issueTypes = ref([])
const issueTypeById = ref({})
const projectUsers = ref([])
const userById = ref({})

// Filters
const filters = ref({
  search: '',
  status: [],
  type: [],
  assignee: [],
  priority: [],
  dateRange: '',
  tags: []
})

// Computed properties
const activeFiltersCount = computed(() => {
  let count = 0
  if (filters.value.search) count++
  if (filters.value.status.length) count++
  if (filters.value.type.length) count++
  if (filters.value.assignee.length) count++
  if (filters.value.priority.length) count++
  if (filters.value.dateRange) count++
  if (filters.value.tags.length) count++
  return count
})

const filteredIssues = computed(() => {
  let filtered = [...totalIssues.value]

  // Sanitize multi-selects: ignore empty ("All ...") values
   const selectedStatuses = Array.isArray(filters.value.status) 
    ? filters.value.status.filter(v => v && v !== "") 
    : []
  const selectedTypes = Array.isArray(filters.value.type) 
    ? filters.value.type.filter(v => v && v !== "") 
    : []
  const selectedAssignees = Array.isArray(filters.value.assignee) 
    ? filters.value.assignee.filter(v => v && v !== "") 
    : []
  const selectedPriorities = Array.isArray(filters.value.priority) 
    ? filters.value.priority.filter(v => v && v !== "") 
    : []
  const selectedTags = Array.isArray(filters.value.tags) 
    ? filters.value.tags.filter(v => v && v !== "") 
    : []

  // Search filter
  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    filtered = filtered.filter(issue => 
      issue.title.toLowerCase().includes(search) ||
      issue.key.toLowerCase().includes(search) ||
      (issue.description && issue.description.toLowerCase().includes(search))
    )
  }

  // Status filter
  if (selectedStatuses.length) {
    filtered = filtered.filter(issue => selectedStatuses.includes(issue.status))
  }

  // Type filter
  if (selectedTypes.length) {
    filtered = filtered.filter(issue => selectedTypes.includes(issue.type))
  }

  // Assignee filter
  if (selectedAssignees.length) {
    filtered = filtered.filter(issue => {
      if (selectedAssignees.includes('unassigned')) {
        return !issue.assignee || selectedAssignees.includes(issue.assignee?.id)
      }
      return issue.assignee && selectedAssignees.includes(issue.assignee.id)
    })
  }

  // Priority filter
  if (selectedPriorities.length) {
    filtered = filtered.filter(issue => selectedPriorities.includes(issue.priority))
  }

  // Tag filter
  if (selectedTags.length) {
    filtered = filtered.filter(issue => {
      const issueTagIds = (issue.tags || []).map(tag => tag.id)
      return selectedTags.some(selectedTagId => issueTagIds.includes(selectedTagId))
    })
  }

  // Sort
  filtered.sort((a, b) => {
    let aVal = a[sortField.value]
    let bVal = b[sortField.value]

    if (sortField.value === 'assignee') {
      aVal = a.assignee?.name || 'Unassigned'
      bVal = b.assignee?.name || 'Unassigned'
    }

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = bVal?.toLowerCase() || ''
    }

    if (sortDirection.value === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  return filtered
})

const paginatedIssues = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredIssues.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredIssues.value.length / pageSize.value)
})

const isAllSelected = computed(() => {
  return paginatedIssues.value.length > 0 && 
         paginatedIssues.value.every(issue => selectedIssues.value.includes(issue.id))
})

const isSomeSelected = computed(() => {
  return selectedIssues.value.length > 0 && !isAllSelected.value
})

// Methods
const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const applyFilters = () => {
  currentPage.value = 1
}

const clearAllFilters = () => {
  filters.value = {
    search: '',
    status: [],
    type: [],
    assignee: [],
    priority: [],
    dateRange: '',
    tags: []
  }
  currentPage.value = 1
}

const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIssues.value = selectedIssues.value.filter(id => 
      !paginatedIssues.value.some(issue => issue.id === id)
    )
  } else {
    paginatedIssues.value.forEach(issue => {
      if (!selectedIssues.value.includes(issue.id)) {
        selectedIssues.value.push(issue.id)
      }
    })
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

const selectIssue = (issueId, event) => {
  if (!event.ctrlKey && !event.metaKey) return
  toggleIssueSelection(issueId)
}

const clearSelection = () => {
  selectedIssues.value = []
  bulkAction.value = ''
}

const applyBulkAction = () => {
  console.log(`Applying ${bulkAction.value} to ${selectedIssues.value.length} issues`)
  // Implement bulk action logic here
  clearSelection()
}

const openIssue = (issue) => {
  selectedIssueDetails.value = issue
}

const closeIssueModal = () => {
  selectedIssueDetails.value = null
}

// Edit Issue
const isEditModalOpen = ref(false)
const editIssueData = ref(null)

const editIssue = async (issue) => {
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    // Fetch latest full issue payload compatible with AddIssueView
    const res = await axios.get(`/api/issues/${issue.id}/`)
    editIssueData.value = res.data
    isEditModalOpen.value = true
  } catch (e) {
    console.error('Failed to load issue for edit:', e)
  }
}

const handleIssueEdited = async () => {
  isEditModalOpen.value = false
  editIssueData.value = null
  await fetchIssues()
}

// Delete Issue with confirmation modal
const isDeleteModalOpen = ref(false)
const issuePendingDelete = ref(null)

const requestDeleteIssue = (issue) => {
  issuePendingDelete.value = issue
  isDeleteModalOpen.value = true
}

const cancelDeleteIssue = () => {
  issuePendingDelete.value = null
  isDeleteModalOpen.value = false
}

const confirmDeleteIssue = async () => {
  if (!issuePendingDelete.value) return
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    await axios.delete(`/api/issues/${issuePendingDelete.value.id}/`)
    // Remove locally and refresh
    totalIssues.value = totalIssues.value.filter(i => i.id !== issuePendingDelete.value.id)
    selectedIssueDetails.value = null
  } catch (e) {
    console.error('Failed to delete issue:', e)
  } finally {
    cancelDeleteIssue()
  }
}

const exportIssues = () => {
  console.log('Exporting issues...')
  // Implement export logic
}

const saveCurrentView = () => {
  console.log('Saving current view...')
  // Implement save view logic
}

// Utility methods
const getTypeIcon = (type) => {
  const icons = { 'Story': '📝', 'Bug': '🐛', 'Task': '✅', 'Epic': '📚' }
  return icons[type] || '📄'
}

const getPriorityIcon = (priority) => {
  const icons = { 'Critical': '🔥', 'High': '🔴', 'Medium': '🟡', 'Low': '🔵' }
  return icons[priority] || '⚪'
}

const getStatusClass = (status) => {
  const classes = {
    'todo': 'status-todo',
    'inprogress': 'status-progress',
    'review': 'status-review',
    'done': 'status-done'
  }
  return classes[status] || ''
}

const getStatusDisplay = (status) => {
  const displays = {
    'todo': 'To Do',
    'inprogress': 'In Progress',
    'review': 'Review',
    'done': 'Done'
  }
  return displays[status] || status
}

const addTagFilter = (tagId) => {
  if (!Array.isArray(filters.value.tags)) {
    filters.value.tags = []
  }
  
  if (!filters.value.tags.includes(tagId)) {
    filters.value.tags.push(tagId)
    applyFilters()
  }
  showTagFilter.value = false
}


const removeTagFilter = (tagId) => {
  if (!Array.isArray(filters.value.tags)) {
    filters.value.tags = []
    return
  }
  
  filters.value.tags = filters.value.tags.filter(id => id !== tagId)
  applyFilters()
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const d = new Date(dateString)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleDateString()
}

const getLabelColor = (label) => {
  const colors = {
    'security': '#e74c3c',
    'auth': '#3498db',
    'ui': '#9b59b6',
    'responsive': '#f39c12',
    'theme': '#2ecc71',
    'performance': '#e67e22',
    'database': '#34495e',
    'profile': '#1abc9c',
    'bug': '#e74c3c',
    'notifications': '#f1c40f',
    'api': '#8e44ad',
    'onboarding': '#16a085',
    'ux': '#27ae60'
  }
  return colors[label] || '#95a5a6'
}

const onIssueCreated = (issueData) => {
  // Optionally refresh issues or show a toast
  showAddIssueModal.value = false
  fetchIssues()
}

// Backend integrations
const fetchIssueTypes = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get('/api/issue-types/')
  issueTypes.value = res.data
  const map = {}
  res.data.forEach(t => { map[t.id] = t })
  issueTypeById.value = map
}

const fetchProjectUsers = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/users/`)
  projectUsers.value = res.data
  teamMembers.value = res.data.map(u => ({
    id: u.id,
    name: (u.first_name || u.last_name) ? `${u.first_name || ''} ${u.last_name || ''}`.trim() : (u.email || 'User'),
    avatar: ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase() || 'U'
  }))
  const map = {}
  teamMembers.value.forEach(u => { map[u.id] = u })
  userById.value = map
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

const normalizeStatus = (backendStatus) => {
  const s = String(backendStatus || '').toLowerCase()
  if (s === 'to_do' || s === 'todo') return 'todo'
  if (s === 'in_progress' || s === 'inprogress') return 'inprogress'
  if (s === 'done') return 'done'
  return s || 'todo'
}

const toTitleCase = (str) => str ? str.charAt(0).toUpperCase() + str.slice(1) : ''

const transformIssue = (raw) => {
  const typeObj = issueTypeById.value[String(raw.issue_type)] || {}
  const assignee = raw.assignee ? userById.value[String(raw.assignee)] : null
  return {
    id: raw.id,
    key: raw.key,
    title: raw.title,
    description: raw.description,
    type: typeObj.name || 'Task',
    status: normalizeStatus(raw.status),
    priority: toTitleCase(raw.priority || 'Medium'),
    storyPoints: raw.story_points ?? null,
    assignee: assignee ? { id: assignee.id, name: assignee.name, avatar: assignee.avatar } : null,
    created: raw.created_at || null,
    labels: [],
    tags: raw.tags || []
  }
}

const fetchIssues = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/`)
  totalIssues.value = res.data.map(transformIssue)
}

onMounted(async () => {
  await fetchIssueTypes()
  await fetchProjectUsers()
  await fetchIssues()
  await fetchTags()
})

watch(currentProject, async () => {
  await fetchIssueTypes()
  await fetchProjectUsers()
  await fetchIssues()
  await fetchTags()
})

</script>

<template>
  <div v-if="!currentProject" class="no-projects-message">
    <h2>No projects found</h2>
    <p>Create your first project to get started!</p>
    <button class="btn btn-primary" @click="$router.push('/create-project')">+ Create Project</button>
  </div>
  <div v-else class="issues-container">
    <!-- Issues Header -->
    <div class="issues-header">
      <div class="header-title">
        <h1>Issues</h1>
        <p class="issues-count">{{ filteredIssues.length }} of {{ totalIssues.length }} issues</p>
      </div>
      
      <div class="header-actions">
        <button class="action-btn" @click="toggleFilters">
          🔍 Filters
          <span class="filter-count" v-if="activeFiltersCount > 0">{{ activeFiltersCount }}</span>
        </button>
        <button class="action-btn" @click="exportIssues">
          📤 Export
        </button>
        <button class="action-btn primary" @click="showAddIssueModal = true">
          + Create Issue
        </button>
      </div>
    </div>

    <!-- Advanced Filters Panel -->
    <div v-if="showFilters" class="filters-panel">
      <div class="filters-row">
        <div class="filter-group">
          <label>Search:</label>
          <input 
            type="text" 
            v-model="filters.search" 
            placeholder="Search by title, key, or description..."
            @input="applyFilters"
          />
        </div>
        
        <div class="filter-group">
          <label>Status:</label>
          <select v-model="filters.status" @change="applyFilters" multiple>
            <option value="">All Statuses</option>
            <option value="todo">To Do</option>
            <option value="inprogress">In Progress</option>
            <option value="review">Review</option>
            <option value="done">Done</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Type:</label>
          <select v-model="filters.type" @change="applyFilters" multiple>
            <option value="">All Types</option>
            <option value="Story">Story</option>
            <option value="Bug">Bug</option>
            <option value="Task">Task</option>
            <option value="Epic">Epic</option>
          </select>
        </div>
      </div>
      
      <div class="filters-row">
        <div class="filter-group">
          <label>Assignee:</label>
          <select v-model="filters.assignee" @change="applyFilters" multiple>
            <option value="">All Assignees</option>
            <option value="unassigned">Unassigned</option>
            <option v-for="user in teamMembers" :key="user.id" :value="user.id">
              {{ user.name }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Priority:</label>
          <select v-model="filters.priority" @change="applyFilters" multiple>
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Created:</label>
          <select v-model="filters.dateRange" @change="applyFilters">
            <option value="">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
          </select>
        </div>

        
        <div class="filter-group">
          <label>Tags:</label>
          <div class="tag-filter-container">
            <div class="visual-tag-selector">
              <!-- Only show this div if there are actually selected tags -->
              <div class="selected-filter-tags" v-if="filters.tags && filters.tags.length > 0">
                <span 
                  v-for="tagId in filters.tags" 
                  :key="tagId"
                  class="filter-tag-chip"
                  :style="{ backgroundColor: availableTags.find(t => t.id === tagId)?.color }"
                >
                  {{ availableTags.find(t => t.id === tagId)?.name }}
                  <button @click="removeTagFilter(tagId)" class="remove-tag-filter">×</button>
                </span>
              </div>
              
              <div class="tag-dropdown-container">
                <button 
                  type="button" 
                  class="tag-filter-btn"
                  @click="showTagFilter = !showTagFilter"
                >
                  Add Tag Filter
                  <span v-if="filters.tags && filters.tags.length > 0" class="tag-count">
                    ({{ filters.tags.length }})
                  </span>
                </button>
                
                <div v-if="showTagFilter" class="tag-filter-dropdown">
                  <div 
                    v-for="tag in availableTags.filter(t => !filters.tags.includes(t.id))" 
                    :key="tag.id"
                    class="tag-filter-option"
                    @click="addTagFilter(tag.id)"
                  >
                    <div class="tag-color-dot" :style="{ backgroundColor: tag.color }"></div>
                    <span>{{ tag.name }}</span>
                  </div>
                  <div v-if="availableTags.filter(t => !filters.tags.includes(t.id)).length === 0" class="no-more-tags">
                    All tags are already selected
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="filters-actions">
        <button class="clear-btn" @click="clearAllFilters">Clear All Filters</button>
        <button class="save-btn" @click="saveCurrentView">Save Current View</button>
      </div>
    </div>

    <!-- Bulk Actions Bar -->
    <div v-if="selectedIssues.length > 0" class="bulk-actions-bar">
      <div class="bulk-info">
        <span>{{ selectedIssues.length }} issues selected</span>
      </div>
      <div class="bulk-actions">
        <select v-model="bulkAction" class="bulk-select">
          <option value="">Bulk Actions</option>
          <option value="assign">Assign To</option>
          <option value="status">Change Status</option>
          <option value="priority">Change Priority</option>
          <option value="delete">Delete</option>
        </select>
        <button class="apply-btn" @click="applyBulkAction" :disabled="!bulkAction">
          Apply
        </button>
        <button class="cancel-btn" @click="clearSelection">
          Cancel
        </button>
      </div>
    </div>

    <!-- Issues Table -->
    <div class="issues-table-container">
      <table class="issues-table">
        <thead>
          <tr>
            <th class="select-column">
              <input 
                type="checkbox" 
                @change="toggleSelectAll"
                :checked="isAllSelected"
                :indeterminate="isSomeSelected"
              />
            </th>
            <th class="sortable" @click="sortBy('key')">
              Key
              <span class="sort-indicator" v-if="sortField === 'key'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('title')">
              Summary
              <span class="sort-indicator" v-if="sortField === 'title'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('type')">
              Type
              <span class="sort-indicator" v-if="sortField === 'type'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('status')">
              Status
              <span class="sort-indicator" v-if="sortField === 'status'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('priority')">
              Priority
              <span class="sort-indicator" v-if="sortField === 'priority'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('assignee')">
              Assignee
              <span class="sort-indicator" v-if="sortField === 'assignee'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('storyPoints')">
              Points
              <span class="sort-indicator" v-if="sortField === 'storyPoints'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th class="sortable" @click="sortBy('created')">
              Created
              <span class="sort-indicator" v-if="sortField === 'created'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="issue in paginatedIssues" 
            :key="issue.id"
            class="issue-row"
            :class="{ 
              'selected': selectedIssues.includes(issue.id),
              'high-priority': issue.priority === 'Critical' || issue.priority === 'High'
            }"
            @click="selectIssue(issue.id, $event)"
          >
            <td class="select-cell">
              <input 
                type="checkbox" 
                :checked="selectedIssues.includes(issue.id)"
                @change="toggleIssueSelection(issue.id)"
                @click.stop
              />
            </td>
            <td class="key-cell">
              <span class="issue-key" @click.stop="openIssue(issue)">{{ issue.key }}</span>
            </td>
            <td class="title-cell">
              <div class="title-content">
                <span class="issue-title" @click.stop="openIssue(issue)">{{ issue.title }}</span>
                <div class="issue-labels" v-if="issue.labels && issue.labels.length">
                  <span 
                    v-for="label in issue.labels" 
                    :key="label"
                    class="label"
                    :style="{ backgroundColor: getLabelColor(label) }"
                  >
                    {{ label }}
                  </span>
                </div>
              </div>
            </td>
            <td class="type-cell">
              <span class="type-badge" :class="issue.type.toLowerCase()">
                {{ getTypeIcon(issue.type) }} {{ issue.type }}
              </span>
            </td>
            <td class="status-cell">
              <span class="status-badge" :class="getStatusClass(issue.status)">
                {{ getStatusDisplay(issue.status) }}
              </span>
            </td>
            <td class="priority-cell">
              <span class="priority-badge" :class="issue.priority.toLowerCase()">
                {{ getPriorityIcon(issue.priority) }} {{ issue.priority }}
              </span>
            </td>
            <td class="assignee-cell">
              <div v-if="issue.assignee" class="assignee-info">
                <div class="assignee-avatar" :title="issue.assignee.name">
                  {{ issue.assignee.avatar }}
                </div>
                <span class="assignee-name">{{ issue.assignee.name }}</span>
              </div>
              <span v-else class="unassigned">Unassigned</span>
            </td>
            <td class="points-cell">
              <span v-if="issue.storyPoints" class="story-points">{{ issue.storyPoints }}</span>
              <span v-else class="no-points">-</span>
            </td>
            <td class="date-cell">
              <span class="created-date">{{ formatDate(issue.created) }}</span>
            </td>
            <td class="actions-cell">
              <div class="issue-actions">
                <button class="action-icon" @click.stop="openIssue(issue)" title="View">
                  👁️
                </button>
                <button class="action-icon" @click.stop="editIssue(issue)" title="Edit">
                  ✏️
                </button>
                <button class="action-icon" @click.stop="requestDeleteIssue(issue)" title="Delete">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination-container">
      <div class="pagination-info">
        Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, filteredIssues.length) }} 
        of {{ filteredIssues.length }} issues
      </div>
      
      <div class="pagination-controls">
        <select v-model="pageSize" @change="currentPage = 1" class="page-size-select">
          <option value="10">10 per page</option>
          <option value="25">25 per page</option>
          <option value="50">50 per page</option>
          <option value="100">100 per page</option>
        </select>
        
        <div class="page-buttons">
          <button 
            class="page-btn" 
            @click="currentPage = 1" 
            :disabled="currentPage === 1"
          >
            First
          </button>
          <button 
            class="page-btn" 
            @click="currentPage--" 
            :disabled="currentPage === 1"
          >
            Previous
          </button>
          
          <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
          
          <button 
            class="page-btn" 
            @click="currentPage++" 
            :disabled="currentPage === totalPages"
          >
            Next
          </button>
          <button 
            class="page-btn" 
            @click="currentPage = totalPages" 
            :disabled="currentPage === totalPages"
          >
            Last
          </button>
        </div>
      </div>
    </div>

    <!-- Issue Details Modal -->
    <div v-if="selectedIssueDetails" class="modal-overlay" @click="closeIssueModal">
      <div class="issue-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedIssueDetails.key }}: {{ selectedIssueDetails.title }}</h2>
          <button class="close-btn" @click="closeIssueModal">×</button>
        </div>
        
        <div class="modal-content">
          <div class="issue-details-grid">
            <div class="detail-item">
              <label>Type:</label>
              <span class="type-badge" :class="selectedIssueDetails.type.toLowerCase()">
                {{ getTypeIcon(selectedIssueDetails.type) }} {{ selectedIssueDetails.type }}
              </span>
            </div>
            
            <div class="detail-item">
              <label>Status:</label>
              <span class="status-badge" :class="getStatusClass(selectedIssueDetails.status)">
                {{ getStatusDisplay(selectedIssueDetails.status) }}
              </span>
            </div>
            
            <div class="detail-item">
              <label>Priority:</label>
              <span class="priority-badge" :class="selectedIssueDetails.priority.toLowerCase()">
                {{ getPriorityIcon(selectedIssueDetails.priority) }} {{ selectedIssueDetails.priority }}
              </span>
            </div>
            
            <div class="detail-item">
              <label>Assignee:</label>
              <div v-if="selectedIssueDetails.assignee" class="assignee-info">
                <div class="assignee-avatar">{{ selectedIssueDetails.assignee.avatar }}</div>
                <span>{{ selectedIssueDetails.assignee.name }}</span>
              </div>
              <span v-else class="unassigned">Unassigned</span>
            </div>
            
            <div class="detail-item" v-if="selectedIssueDetails.storyPoints">
              <label>Story Points:</label>
              <span class="story-points">{{ selectedIssueDetails.storyPoints }}</span>
            </div>
            
            <div class="detail-item">
              <label>Created:</label>
              <span>{{ formatDate(selectedIssueDetails.created) }}</span>
            </div>

                        <!-- In the issue-details-grid section, add this: -->
            <div class="detail-item" v-if="selectedIssueDetails.tags && selectedIssueDetails.tags.length">
              <label>Tags:</label>
              <div class="modal-tags">
                <span 
                  v-for="tag in selectedIssueDetails.tags" 
                  :key="tag.id"
                  class="modal-tag"
                  :style="{ backgroundColor: tag.color }"
                >
                  {{ tag.name }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="description-section">
            <label>Description:</label>
            <p class="description-text">
              {{ selectedIssueDetails.description || 'No description provided.' }}
            </p>
          </div>

          <IssueComments v-if="selectedIssueDetails?.id" :issueId="selectedIssueDetails.id" />
          
          <div class="modal-actions">
            <button class="action-btn" @click="editIssue(selectedIssueDetails)">Edit Issue</button>
            <button class="action-btn danger" @click="deleteIssue(selectedIssueDetails)">Delete Issue</button>
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

  <!-- Edit Issue Modal reuse -->
  <AddIssueView
    :showModal="isEditModalOpen"
    mode="edit"
    :issue="editIssueData"
    @close="() => { isEditModalOpen = false; editIssueData = null }"
    @save="handleIssueEdited"
  />

  <!-- Delete Confirmation Modal -->
  <div v-if="isDeleteModalOpen" class="modal-overlay" @click="cancelDeleteIssue">
    <div class="issue-modal" @click.stop>
      <div class="modal-header">
        <h2>Delete Issue</h2>
        <button class="close-btn" @click="cancelDeleteIssue">×</button>
      </div>
      <div class="modal-content">
        <p>Are you sure you want to delete <strong>{{ issuePendingDelete?.key }}</strong>? This action cannot be undone.</p>
      </div>
      <div class="modal-actions">
        <button class="action-btn" @click="cancelDeleteIssue">Cancel</button>
        <button class="action-btn danger" @click="confirmDeleteIssue">Delete</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.issues-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header Styles */
.issues-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e4e8;
}

.header-title h1 {
  margin: 0 0 0.25rem 0;
  color: #24292e;
  font-size: 1.75rem;
  font-weight: 600;
}

.issues-count {
  margin: 0;
  color: #586069;
  font-size: 0.875rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.action-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  background: #fafbfc;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.875rem;
  font-weight: 500;
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #24292e;
}

.action-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5da;
}

.action-btn.primary {
  background: #2ea043;
  color: white;
  border-color: #2ea043;
}

.action-btn.primary:hover {
  background: #2c974b;
  border-color: #2c974b;
}

.filter-count {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #d73a49;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

/* Filters Panel */
.filters-panel {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filters-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.filters-row:last-of-type {
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
  color: #24292e;
  font-size: 0.875rem;
}

.filter-group input,
.filter-group select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
}

.filter-group input:focus,
.filter-group select:focus {
  border-color: #0969da;
  outline: none;
  box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
}

.filters-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.clear-btn, .save-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.clear-btn:hover {
  background: #f6f8fa;
}

.save-btn {
  background: #0969da;
  color: white;
  border-color: #0969da;
}

.save-btn:hover {
  background: #0860ca;
}

/* Bulk Actions Bar */
.bulk-actions-bar {
  background: #fff8c5;
  border: 1px solid #d4c5f9;
  border-radius: 6px;
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bulk-info {
  font-weight: 500;
  color: #735c0f;
}

.bulk-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.bulk-select {
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 0.875rem;
}

.apply-btn, .cancel-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.apply-btn {
  background: #2ea043;
  color: white;
  border-color: #2ea043;
}

.apply-btn:hover:not(:disabled) {
  background: #2c974b;
}

.apply-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-btn {
  background: white;
  color: #24292e;
}

.cancel-btn:hover {
  background: #f6f8fa;
}

/* Issues Table */
.issues-table-container {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.issues-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.issues-table th {
  background: #f6f8fa;
  border-bottom: 1px solid #e1e4e8;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #24292e;
  position: relative;
}

.issues-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.issues-table th.sortable:hover {
  background: #f1f3f4;
}

.sort-indicator {
  margin-left: 0.5rem;
  color: #0969da;
  font-weight: bold;
}

.issues-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e1e4e8;
  vertical-align: middle;
}

.issue-row {
  transition: background-color 0.15s ease;
  cursor: pointer;
}

.issue-row:hover {
  background: #f6f8fa;
}

.issue-row.selected {
  background: #dbeafe !important;
}

.issue-row.high-priority {
  border-left: 4px solid #ff6b6b;
}

/* Table Cell Styles */
.select-column {
  width: 40px;
}

.select-cell input[type="checkbox"] {
  cursor: pointer;
}

.key-cell {
  width: 100px;
}

.issue-key {
  color: #0969da;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.issue-key:hover {
  text-decoration: underline;
}

.title-cell {
  min-width: 250px;
}

.title-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.issue-title {
  color: #24292e;
  font-weight: 500;
  cursor: pointer;
  line-height: 1.3;
}

.issue-title:hover {
  color: #0969da;
}

.issue-labels {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.label {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  color: white;
}

/* Badge Styles */
.type-badge, .status-badge, .priority-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

/* Type Badges */
.type-badge.story { background: #e3f2fd; color: #1565c0; }
.type-badge.bug { background: #ffebee; color: #c62828; }
.type-badge.task { background: #e8f5e8; color: #2e7d32; }
.type-badge.epic { background: #f3e5f5; color: #7b1fa2; }

/* Status Badges */
.status-badge.status-todo { background: #f1f3f4; color: #5f6368; }
.status-badge.status-progress { background: #fff3cd; color: #856404; }
.status-badge.status-review { background: #d1ecf1; color: #0c5460; }
.status-badge.status-done { background: #d4edda; color: #155724; }

/* Priority Badges */
.priority-badge.critical { background: #ffebee; color: #c62828; }
.priority-badge.high { background: #fff3e0; color: #ef6c00; }
.priority-badge.medium { background: #fff8e1; color: #f57f17; }
.priority-badge.low { background: #e3f2fd; color: #1565c0; }

/* Assignee Styles */
.assignee-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.assignee-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #0969da;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.assignee-name {
  font-weight: 500;
  color: #24292e;
}

.unassigned {
  color: #656d76;
  font-style: italic;
}

/* Points and Date */
.story-points {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f6f8fa;
  border: 2px solid #d1d5da;
  font-weight: 600;
  color: #24292e;
}

.no-points {
  color: #656d76;
}

.created-date {
  color: #656d76;
  font-size: 0.8125rem;
}

/* Actions */
.issue-actions {
  display: flex;
  gap: 0.25rem;
}

.action-icon {
  padding: 0.25rem;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.875rem;
  transition: background-color 0.15s ease;
}

.action-icon:hover {
  background: #f6f8fa;
}

/* Pagination */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 1rem 1.5rem;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination-info {
  color: #656d76;
  font-size: 0.875rem;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.page-size-select {
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 0.875rem;
}

.page-buttons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.page-btn:hover:not(:disabled) {
  background: #f6f8fa;
}

.page-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.page-info {
  color: #24292e;
  font-weight: 500;
  margin: 0 0.5rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(27, 31, 36, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.issue-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid #e1e4e8;
}

.modal-header h2 {
  margin: 0;
  color: #24292e;
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.4;
  padding-right: 1rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #656d76;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: #f6f8fa;
  color: #24292e;
}

.modal-content {
  padding: 1.5rem;
  overflow-y: auto;
}

.issue-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-item label {
  font-weight: 600;
  color: #656d76;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.description-section {
  margin-bottom: 1.5rem;
}

.description-section label {
  font-weight: 600;
  color: #656d76;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  display: block;
  margin-bottom: 0.75rem;
}

.description-text {
  color: #24292e;
  line-height: 1.6;
  margin: 0;
  padding: 1rem;
  background: #f6f8fa;
  border-radius: 6px;
  border: 1px solid #e1e4e8;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #e1e4e8;
}

.modal-actions .action-btn.danger {
  background: #d73a49;
  color: white;
  border-color: #d73a49;
}

.modal-actions .action-btn.danger:hover {
  background: #cb2431;
  border-color: #cb2431;
}
.tag-filter-container {
  position: relative;
}

.visual-tag-selector {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selected-filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.filter-tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
}

.remove-tag-filter {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0;
  margin-left: 0.25rem;
}

.tag-dropdown-container {
  position: relative;
}

.tag-filter-btn {
  padding: 0.5rem 0.75rem;
  border: 1px dashed #d1d5da;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  color: #656d76;
}

.tag-filter-btn:hover {
  border-color: #0969da;
  color: #0969da;
}

.tag-filter-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(140, 149, 159, 0.2);
  z-index: 10;
  max-height: 200px;
  overflow-y: auto;
}

.tag-filter-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f6f8fa;
  transition: background-color 0.15s ease;
}

.tag-filter-option:hover {
  background: #f6f8fa;
}

.tag-filter-option:last-child {
  border-bottom: none;
}

.tag-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

/* Modal Tags */
.modal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.modal-tag {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
}

.tag-count {
  color: #0969da;
  font-weight: 600;
  margin-left: 0.25rem;
}

.no-more-tags {
  padding: 0.75rem;
  color: #656d76;
  font-style: italic;
  text-align: center;
  font-size: 0.875rem;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .issues-table-container {
    overflow-x: auto;
  }

  .issues-table {
    min-width: 800px;
  }
}

@media (max-width: 768px) {
  .issues-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: flex-end;
  }

  .filters-row {
    grid-template-columns: 1fr;
  }

  .bulk-actions-bar {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .pagination-container {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .pagination-controls {
    justify-content: center;
  }

  .issue-modal {
    width: 95%;
    margin: 20px;
  }
}


/* Add this to your existing <style scoped> section */

@media (prefers-color-scheme: dark) {
  /* Container */
  .issues-container {
    background: #0d1117;
    color: #c9d1d9;
  }

  /* Header Styles */
  .issues-header {
    background: #161b22 !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .header-title h1 {
    color: #f0f6fc !important;
  }

  .issues-count {
    color: #8b949e !important;
  }

  .action-btn {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .action-btn:hover {
    background: #30363d !important;
    border-color: #484f58 !important;
  }

  .action-btn.primary {
    background: #238636 !important;
    border-color: #238636 !important;
    color: #ffffff !important;
  }

  .action-btn.primary:hover {
    background: #2ea043 !important;
    border-color: #2ea043 !important;
  }

  .filter-count {
    background: #da3633 !important;
    color: #ffffff !important;
  }

  /* Filters Panel */
  .filters-panel {
    background: #161b22 !important;
    border-color: #30363d !important;
  }

  .filter-group label {
    color: #f0f6fc !important;
  }

  .filter-group input,
  .filter-group select {
    background: #0d1117 !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .filter-group input:focus,
  .filter-group select:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.3) !important;
  }

  .clear-btn, .save-btn {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .clear-btn:hover {
    background: #30363d !important;
  }

  .save-btn {
    background: #1f6feb !important;
    border-color: #1f6feb !important;
    color: #ffffff !important;
  }

  .save-btn:hover {
    background: #1a5ee8 !important;
  }

  /* Bulk Actions Bar */
  .bulk-actions-bar {
    background: #1c2128 !important;
    border-color: #373e47 !important;
  }

  .bulk-info {
    color: #d29922 !important;
  }

  .bulk-select {
    background: #0d1117 !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .apply-btn {
    background: #238636 !important;
    border-color: #238636 !important;
    color: #ffffff !important;
  }

  .apply-btn:hover:not(:disabled) {
    background: #2ea043 !important;
  }

  .cancel-btn {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .cancel-btn:hover {
    background: #30363d !important;
  }

  /* Issues Table */
  .issues-table-container {
    background: #161b22 !important;
    border-color: #30363d !important;
  }

  .issues-table th {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #f0f6fc !important;
  }

  .issues-table th.sortable:hover {
    background: #30363d !important;
  }

  .sort-indicator {
    color: #58a6ff !important;
  }

  .issues-table td {
    border-color: #30363d !important;
  }

  .issue-row:hover {
    background: #21262d !important;
  }

  .issue-row.selected {
    background: #0c2d6b !important;
  }

  .issue-row.high-priority {
    border-left-color: #f85149 !important;
  }

  /* Table Cell Styles */
  .select-cell input[type="checkbox"] {
    accent-color: #1f6feb;
  }

  .issue-key {
    color: #58a6ff !important;
  }

  .issue-key:hover {
    color: #79c0ff !important;
  }

  .issue-title {
    color: #c9d1d9 !important;
  }

  .issue-title:hover {
    color: #58a6ff !important;
  }

  /* Badge Styles - Dark Mode Updates */
  .type-badge.story { 
    background: #1a2332 !important; 
    color: #79c0ff !important; 
  }
  
  .type-badge.bug { 
    background: #2d1b20 !important; 
    color: #ff7b72 !important; 
  }
  
  .type-badge.task { 
    background: #1b2718 !important; 
    color: #7ee787 !important; 
  }
  
  .type-badge.epic { 
    background: #2b1a2e !important; 
    color: #d2a8ff !important; 
  }

  /* Status Badges */
  .status-badge.status-todo { 
    background: #21262d !important; 
    color: #8b949e !important; 
  }
  
  .status-badge.status-progress { 
    background: #2d2408 !important; 
    color: #f0cc81 !important; 
  }
  
  .status-badge.status-review { 
    background: #0a2540 !important; 
    color: #79c0ff !important; 
  }
  
  .status-badge.status-done { 
    background: #1b2718 !important; 
    color: #7ee787 !important; 
  }

  /* Priority Badges */
  .priority-badge.critical { 
    background: #2d1b20 !important; 
    color: #ff7b72 !important; 
  }
  
  .priority-badge.high { 
    background: #2d1e0a !important; 
    color: #ffa657 !important; 
  }
  
  .priority-badge.medium { 
    background: #2d2408 !important; 
    color: #f0cc81 !important; 
  }
  
  .priority-badge.low { 
    background: #1a2332 !important; 
    color: #79c0ff !important; 
  }

  /* Assignee Styles */
  .assignee-avatar {
    background: #1f6feb !important;
    color: #ffffff !important;
  }

  .assignee-name {
    color: #c9d1d9 !important;
  }

  .unassigned {
    color: #8b949e !important;
  }

  /* Points and Date */
  .story-points {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .no-points {
    color: #8b949e !important;
  }

  .created-date {
    color: #8b949e !important;
  }

  /* Actions */
  .action-icon:hover {
    background: #30363d !important;
  }

  /* Pagination */
  .pagination-container {
    background: #161b22 !important;
    border-color: #30363d !important;
  }

  .pagination-info {
    color: #8b949e !important;
  }

  .page-size-select {
    background: #0d1117 !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .page-btn {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .page-btn:hover:not(:disabled) {
    background: #30363d !important;
  }

  .page-info {
    color: #c9d1d9 !important;
  }

  /* Modal Styles */
  .modal-overlay {
    background: rgba(1, 4, 9, 0.8) !important;
  }

  .issue-modal {
    background: #161b22 !important;
    border-color: #30363d !important;
    box-shadow: 0 25px 50px -12px rgba(1, 4, 9, 0.4) !important;
  }

  .modal-header {
    border-color: #30363d !important;
  }

  .modal-header h2 {
    color: #f0f6fc !important;
  }

  .close-btn {
    color: #8b949e !important;
  }

  .close-btn:hover {
    background: #30363d !important;
    color: #c9d1d9 !important;
  }

  .detail-item label {
    color: #8b949e !important;
  }

  .description-section label {
    color: #8b949e !important;
  }

  .description-text {
    background: #0d1117 !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .modal-actions {
    border-color: #30363d !important;
  }

  .modal-actions .action-btn.danger {
    background: #da3633 !important;
    border-color: #da3633 !important;
    color: #ffffff !important;
  }

  .modal-actions .action-btn.danger:hover {
    background: #f85149 !important;
    border-color: #f85149 !important;
  }

  /* Label colors for dark mode */
  .label {
    opacity: 0.9;
  }

  /* Scrollbar styling for dark mode */
  .issues-table-container::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  .issues-table-container::-webkit-scrollbar-track {
    background: #21262d;
  }

  .issues-table-container::-webkit-scrollbar-thumb {
    background: #484f58;
    border-radius: 4px;
  }

  .issues-table-container::-webkit-scrollbar-thumb:hover {
    background: #6e7681;
  }

  /* Focus states for better accessibility in dark mode */
  .issues-table th.sortable:focus {
    outline: 2px solid #58a6ff;
    outline-offset: 2px;
  }

  .issue-row:focus-within {
    outline: 1px solid #30363d;
  }

  .tag-filter-btn {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #8b949e !important;
  }

  .tag-filter-btn:hover {
    border-color: #58a6ff !important;
    color: #58a6ff !important;
  }

  .tag-filter-dropdown {
    background: #161b22 !important;
    border-color: #30363d !important;
    box-shadow: 0 8px 24px rgba(1, 4, 9, 0.3) !important;
  }

  .tag-filter-option {
    border-color: #21262d !important;
    color: #c9d1d9 !important;
  }

  .tag-filter-option:hover {
    background: #21262d !important;
  }

  .tag-count {
    color: #58a6ff !important;
  }

  .no-more-tags {
    color: #8b949e !important;
  }
  
}
</style>