<template>
  <div class="issues-container">
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
        <button class="action-btn primary" @click="showCreateModal = true">
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
                <button class="action-icon" @click.stop="deleteIssue(issue)" title="Delete">
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
          </div>
          
          <div class="description-section">
            <label>Description:</label>
            <p class="description-text">
              {{ selectedIssueDetails.description || 'No description provided.' }}
            </p>
          </div>
          
          <div class="modal-actions">
            <button class="action-btn" @click="editIssue(selectedIssueDetails)">Edit Issue</button>
            <button class="action-btn danger" @click="deleteIssue(selectedIssueDetails)">Delete Issue</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Data
const showFilters = ref(false)
const showCreateModal = ref(false)
const selectedIssueDetails = ref(null)
const selectedIssues = ref([])
const bulkAction = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(25)

// Sorting
const sortField = ref('created')
const sortDirection = ref('desc')

// Team members
const teamMembers = ref([
  { id: 1, name: 'Alice Johnson', avatar: 'AJ' },
  { id: 2, name: 'Bob Smith', avatar: 'BS' },
  { id: 3, name: 'Charlie Brown', avatar: 'CB' },
  { id: 4, name: 'Diana Prince', avatar: 'DP' },
  { id: 5, name: 'Eve Wilson', avatar: 'EW' }
])

// Sample issues data
const totalIssues = ref([
  {
    id: 1, key: 'AP-143', title: 'Implement user authentication system',
    description: 'Create a secure login system with JWT tokens and role-based access control.',
    type: 'Story', status: 'todo', priority: 'High', storyPoints: 8,
    assignee: { id: 1, name: 'Alice Johnson', avatar: 'AJ' },
    created: '2024-01-15', labels: ['security', 'auth']
  },
  {
    id: 2, key: 'AP-144', title: 'Fix navigation menu responsiveness',
    description: 'The navigation menu breaks on mobile devices and needs responsive design fixes.',
    type: 'Bug', status: 'inprogress', priority: 'Critical', storyPoints: 3,
    assignee: { id: 2, name: 'Bob Smith', avatar: 'BS' },
    created: '2024-01-16', labels: ['ui', 'responsive']
  },
  {
    id: 3, key: 'AP-145', title: 'Add dark mode toggle',
    description: 'Implement a dark mode theme switcher in the user preferences.',
    type: 'Task', status: 'review', priority: 'Medium', storyPoints: 5,
    assignee: { id: 3, name: 'Charlie Brown', avatar: 'CB' },
    created: '2024-01-17', labels: ['ui', 'theme']
  },
  {
    id: 4, key: 'AP-146', title: 'Database performance optimization',
    description: 'Optimize slow queries and add proper indexing to improve database performance.',
    type: 'Story', status: 'done', priority: 'High', storyPoints: 13,
    assignee: { id: 4, name: 'Diana Prince', avatar: 'DP' },
    created: '2024-01-18', labels: ['performance', 'database']
  },
  {
    id: 5, key: 'AP-147', title: 'Update user profile page',
    description: 'Redesign the user profile page with better UX and additional fields.',
    type: 'Story', status: 'todo', priority: 'Medium', storyPoints: 8,
    assignee: null,
    created: '2024-01-19', labels: ['ui', 'profile']
  },
  {
    id: 6, key: 'AP-148', title: 'Fix email notification bug',
    description: 'Users are not receiving email notifications for issue assignments.',
    type: 'Bug', status: 'done', priority: 'High', storyPoints: 2,
    assignee: { id: 5, name: 'Eve Wilson', avatar: 'EW' },
    created: '2024-01-20', labels: ['bug', 'notifications']
  },
  {
    id: 7, key: 'AP-149', title: 'Implement API rate limiting',
    description: 'Add rate limiting to prevent API abuse and improve security.',
    type: 'Epic', status: 'todo', priority: 'Low', storyPoints: 21,
    assignee: { id: 1, name: 'Alice Johnson', avatar: 'AJ' },
    created: '2024-01-21', labels: ['api', 'security']
  },
  {
    id: 8, key: 'AP-150', title: 'Create user onboarding flow',
    description: 'Design and implement a guided onboarding process for new users.',
    type: 'Story', status: 'inprogress', priority: 'Medium', storyPoints: 13,
    assignee: { id: 2, name: 'Bob Smith', avatar: 'BS' },
    created: '2024-01-22', labels: ['onboarding', 'ux']
  }
])

// Filters
const filters = ref({
  search: '',
  status: [],
  type: [],
  assignee: [],
  priority: [],
  dateRange: ''
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
  return count
})

const filteredIssues = computed(() => {
  let filtered = [...totalIssues.value]

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
  if (filters.value.status.length) {
    filtered = filtered.filter(issue => filters.value.status.includes(issue.status))
  }

  // Type filter
  if (filters.value.type.length) {
    filtered = filtered.filter(issue => filters.value.type.includes(issue.type))
  }

  // Assignee filter
  if (filters.value.assignee.length) {
    filtered = filtered.filter(issue => {
      if (filters.value.assignee.includes('unassigned')) {
        return !issue.assignee || filters.value.assignee.includes(issue.assignee?.id)
      }
      return issue.assignee && filters.value.assignee.includes(issue.assignee.id)
    })
  }

  // Priority filter
  if (filters.value.priority.length) {
    filtered = filtered.filter(issue => filters.value.priority.includes(issue.priority))
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
    dateRange: ''
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

const editIssue = (issue) => {
  console.log('Editing issue:', issue.key)
  // Implement edit logic
}

const deleteIssue = (issue) => {
  if (confirm(`Are you sure you want to delete ${issue.key}?`)) {
    const index = totalIssues.value.findIndex(i => i.id === issue.id)
    if (index > -1) {
      totalIssues.value.splice(index, 1)
    }
    selectedIssueDetails.value = null
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

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
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
</script>

<style scoped>
.issues-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* Header */
.issues-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-title h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.8rem;
}

.issues-count {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.action-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
  position: relative;
}

.action-btn:hover {
  background: #f8f9fa;
  border-color: #0066cc;
}

.action-btn.primary {
  background: #0066cc;
  color: white;
  border-color: #0066cc;
}

.action-btn.primary:hover {
  background: #0056b3;
}

.filter-count {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.issue-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e4e8;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.issue-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: #24292e;
  margin: 0;
}

.issue-key {
  color: #586069;
  font-size: 0.9rem;
  margin-right: 0.5rem;
}

.issue-type {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.issue-type.story { background: #e3f2fd; color: #1976d2; }
.issue-type.bug { background: #ffebee; color: #d32f2f; }
.issue-type.task { background: #f1f8e9; color: #689f38; }

.issue-priority {
  display: inline-flex;
  align-items: center;
  margin-left: 0.5rem;
}

.issue-priority img {
  width: 16px;
  height: 16px;
}

.issue-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
  color: #586069;
  font-size: 0.9rem;
}

.issue-assignee {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.assignee-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.issue-description {
  color: #444d56;
  margin: 1rem 0;
  line-height: 1.5;
}

.issue-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e1e4e8;
}

.issue-labels {
  display: flex;
  gap: 0.5rem;
}

.issue-label {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  background: #f1f8ff;
  color: #0366d6;
}

/* Form Styles */
.issue-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #24292e;
}

.form-control {
  padding: 0.5rem;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-control:focus {
  border-color: #0366d6;
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
}

/* Comments Section */
.comments-section {
  margin-top: 2rem;
}

.comment {
  padding: 1rem;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.comment-author {
  font-weight: 500;
}

.comment-time {
  color: #586069;
  font-size: 0.9rem;
}

/* Status Tags */
.status-tag {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-todo { background: #f1f8ff; color: #0366d6; }
.status-progress { background: #fff8c5; color: #735c0f; }
.status-done { background: #e6ffec; color: #22863a; }

/* Responsive Design */
@media (max-width: 768px) {
  .issue-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .issue-meta {
    flex-wrap: wrap;
  }
}
</style>