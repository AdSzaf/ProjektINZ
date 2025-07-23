<template>
  <div class="board-container">
    <!-- Board Header -->
    <div class="board-header">
      <div class="board-title">
        <h1>{{ selectedProject.name }} Board</h1>
        <p class="sprint-info">{{ activeSprint.name }} • {{ activeSprint.issues.length }} issues</p>
      </div>
      
      <div class="board-actions">
        <button class="action-btn" @click="showFilters = !showFilters">
          🔍 Filters
        </button>
        <button class="action-btn" @click="toggleGroupBy">
          👥 Group by: {{ groupBy }}
        </button>
        <button class="action-btn primary" @click="showCreateIssue = true">
          + Create Issue
        </button>
      </div>
    </div>

    <!-- Filters Bar -->
    <div v-if="showFilters" class="filters-bar">
      <div class="filter-group">
        <label>Assignee:</label>
        <select v-model="filters.assignee" @change="applyFilters">
          <option value="">All</option>
          <option v-for="user in teamMembers" :key="user.id" :value="user.id">
            {{ user.name }}
          </option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>Type:</label>
        <select v-model="filters.type" @change="applyFilters">
          <option value="">All</option>
          <option value="Story">Story</option>
          <option value="Bug">Bug</option>
          <option value="Task">Task</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>Priority:</label>
        <select v-model="filters.priority" @change="applyFilters">
          <option value="">All</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
      </div>
      
      <button class="clear-filters-btn" @click="clearFilters">Clear All</button>
    </div>

    <!-- Board Columns -->
    <div class="board-content">
      <div class="board-columns">
        <div 
          v-for="column in columns" 
          :key="column.id"
          class="board-column"
          @drop="onDrop($event, column.id)"
          @dragover.prevent
          @dragenter.prevent
        >
          <div class="column-header">
            <h3 class="column-title">{{ column.name }}</h3>
            <span class="issue-count">{{ getColumnIssues(column.id).length }}</span>
          </div>
          
          <div class="column-content">
            <div 
              v-for="issue in getColumnIssues(column.id)" 
              :key="issue.id"
              class="issue-card"
              :class="{ 'dragging': draggingIssue === issue.id }"
              draggable="true"
              @dragstart="onDragStart($event, issue)"
              @dragend="onDragEnd"
              @click="openIssueDetails(issue)"
            >
              <div class="issue-header">
                <div class="issue-type">
                  <span class="type-icon" :class="issue.type.toLowerCase()">
                    {{ getTypeIcon(issue.type) }}
                  </span>
                  <span class="issue-key">{{ issue.key }}</span>
                </div>
                <div class="issue-priority" :class="issue.priority.toLowerCase()">
                  {{ getPriorityIcon(issue.priority) }}
                </div>
              </div>
              
              <div class="issue-title">{{ issue.title }}</div>
              
              <div class="issue-footer">
                <div class="issue-assignee" v-if="issue.assignee">
                  <div class="assignee-avatar" :title="issue.assignee.name">
                    {{ issue.assignee.avatar }}
                  </div>
                </div>
                <div class="issue-points" v-if="issue.storyPoints">
                  {{ issue.storyPoints }}
                </div>
              </div>
            </div>
            
            <!-- Add Issue Button -->
            <button 
              class="add-issue-btn"
              @click="createIssueInColumn(column.id)"
            >
              + Create issue
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Issue Details Modal -->
    <div v-if="selectedIssue" class="modal-overlay" @click="closeIssueDetails">
      <div class="issue-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedIssue.key }}: {{ selectedIssue.title }}</h2>
          <button class="close-btn" @click="closeIssueDetails">×</button>
        </div>
        
        <div class="modal-content">
          <div class="issue-details">
            <div class="detail-row">
              <label>Type:</label>
              <span class="type-badge" :class="selectedIssue.type.toLowerCase()">
                {{ getTypeIcon(selectedIssue.type) }} {{ selectedIssue.type }}
              </span>
            </div>
            
            <div class="detail-row">
              <label>Status:</label>
              <span class="status-badge">{{ selectedIssue.status }}</span>
            </div>
            
            <div class="detail-row">
              <label>Priority:</label>
              <span class="priority-badge" :class="selectedIssue.priority.toLowerCase()">
                {{ getPriorityIcon(selectedIssue.priority) }} {{ selectedIssue.priority }}
              </span>
            </div>
            
            <div class="detail-row">
              <label>Assignee:</label>
              <span v-if="selectedIssue.assignee" class="assignee-info">
                <span class="assignee-avatar">{{ selectedIssue.assignee.avatar }}</span>
                {{ selectedIssue.assignee.name }}
              </span>
              <span v-else class="unassigned">Unassigned</span>
            </div>
            
            <div class="detail-row" v-if="selectedIssue.storyPoints">
              <label>Story Points:</label>
              <span class="story-points">{{ selectedIssue.storyPoints }}</span>
            </div>
            
            <div class="description-section">
              <label>Description:</label>
              <p class="description-text">{{ selectedIssue.description || 'No description provided.' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Props
const selectedProject = ref({
  id: 1,
  name: 'AgilePro',
  key: 'AP'
})

// Data
const showFilters = ref(false)
const showCreateIssue = ref(false)
const selectedIssue = ref(null)
const draggingIssue = ref(null)
const groupBy = ref('Status')

const activeSprint = ref({
  id: 1,
  name: 'Sprint 23',
  issues: []
})

const teamMembers = ref([
  { id: 1, name: 'Alice Johnson', avatar: 'AJ' },
  { id: 2, name: 'Bob Smith', avatar: 'BS' },
  { id: 3, name: 'Charlie Brown', avatar: 'CB' },
  { id: 4, name: 'Diana Prince', avatar: 'DP' }
])

const columns = ref([
  { id: 'todo', name: 'To Do', color: '#ddd' },
  { id: 'inprogress', name: 'In Progress', color: '#007bff' },
  { id: 'review', name: 'Review', color: '#ffc107' },
  { id: 'done', name: 'Done', color: '#28a745' }
])

const issues = ref([
  {
    id: 1,
    key: 'AP-143',
    title: 'Implement user authentication system',
    description: 'Create a secure login system with JWT tokens and role-based access control.',
    type: 'Story',
    status: 'todo',
    priority: 'High',
    storyPoints: 8,
    assignee: { id: 1, name: 'Alice Johnson', avatar: 'AJ' }
  },
  {
    id: 2,
    key: 'AP-144',
    title: 'Fix navigation menu responsiveness',
    description: 'The navigation menu breaks on mobile devices and needs responsive design fixes.',
    type: 'Bug',
    status: 'todo',
    priority: 'Medium',
    storyPoints: 3,
    assignee: { id: 2, name: 'Bob Smith', avatar: 'BS' }
  },
  {
    id: 3,
    key: 'AP-145',
    title: 'Add dark mode toggle',
    description: 'Implement a dark mode theme switcher in the user preferences.',
    type: 'Task',
    status: 'inprogress',
    priority: 'Low',
    storyPoints: 5,
    assignee: { id: 1, name: 'Alice Johnson', avatar: 'AJ' }
  },
  {
    id: 4,
    key: 'AP-146',
    title: 'Database performance optimization',
    description: 'Optimize slow queries and add proper indexing to improve database performance.',
    type: 'Story',
    status: 'inprogress',
    priority: 'High',
    storyPoints: 13,
    assignee: { id: 3, name: 'Charlie Brown', avatar: 'CB' }
  },
  {
    id: 5,
    key: 'AP-147',
    title: 'Update user profile page',
    description: 'Redesign the user profile page with better UX and additional fields.',
    type: 'Story',
    status: 'review',
    priority: 'Medium',
    storyPoints: 5,
    assignee: { id: 4, name: 'Diana Prince', avatar: 'DP' }
  },
  {
    id: 6,
    key: 'AP-148',
    title: 'Fix email notification bug',
    description: 'Users are not receiving email notifications for issue assignments.',
    type: 'Bug',
    status: 'done',
    priority: 'High',
    storyPoints: 2,
    assignee: { id: 2, name: 'Bob Smith', avatar: 'BS' }
  }
])

const filters = ref({
  assignee: '',
  type: '',
  priority: ''
})

// Computed
const filteredIssues = computed(() => {
  let filtered = issues.value

  if (filters.value.assignee) {
    filtered = filtered.filter(issue => 
      issue.assignee && issue.assignee.id === parseInt(filters.value.assignee)
    )
  }

  if (filters.value.type) {
    filtered = filtered.filter(issue => issue.type === filters.value.type)
  }

  if (filters.value.priority) {
    filtered = filtered.filter(issue => issue.priority === filters.value.priority)
  }

  return filtered
})

// Methods
const getColumnIssues = (columnId) => {
  return filteredIssues.value.filter(issue => issue.status === columnId)
}

const getTypeIcon = (type) => {
  const icons = {
    'Story': '📝',
    'Bug': '🐛',
    'Task': '✅'
  }
  return icons[type] || '📄'
}

const getPriorityIcon = (priority) => {
  const icons = {
    'High': '🔴',
    'Medium': '🟡',
    'Low': '🔵'
  }
  return icons[priority] || '⚪'
}

const onDragStart = (event, issue) => {
  draggingIssue.value = issue.id
  event.dataTransfer.setData('text/plain', issue.id.toString())
}

const onDragEnd = () => {
  draggingIssue.value = null
}

const onDrop = (event, columnId) => {
  event.preventDefault()
  const issueId = parseInt(event.dataTransfer.getData('text/plain'))
  const issue = issues.value.find(i => i.id === issueId)
  
  if (issue && issue.status !== columnId) {
    issue.status = columnId
    console.log(`Moved issue ${issue.key} to ${columnId}`)
  }
}

const openIssueDetails = (issue) => {
  selectedIssue.value = issue
}

const closeIssueDetails = () => {
  selectedIssue.value = null
}

const createIssueInColumn = (columnId) => {
  console.log(`Creating new issue in column: ${columnId}`)
  // Implementation for creating new issue
}

const toggleGroupBy = () => {
  const options = ['Status', 'Assignee', 'Priority']
  const currentIndex = options.indexOf(groupBy.value)
  groupBy.value = options[(currentIndex + 1) % options.length]
}

const applyFilters = () => {
  console.log('Applying filters:', filters.value)
}

const clearFilters = () => {
  filters.value = {
    assignee: '',
    type: '',
    priority: ''
  }
}

// Initialize sprint issues count
onMounted(() => {
  activeSprint.value.issues = issues.value
})
</script>

<style scoped>
.board-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background-color: #f8f9fa;
}

/* Board Header */
.board-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.board-title h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.8rem;
}

.sprint-info {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.board-actions {
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

/* Filters Bar */
.filters-bar {
  display: flex;
  gap: 1rem;
  align-items: center;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.filter-group select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.clear-filters-btn {
  padding: 0.25rem 0.75rem;
  background: none;
  border: 1px solid #dc3545;
  color: #dc3545;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.clear-filters-btn:hover {
  background: #dc3545;
  color: white;
}

/* Board Content */
.board-content {
  flex: 1;
  min-height: 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.board-columns {
  display: flex;
  gap: 1rem;
  height: 100%;
  min-width: max-content;
  padding-bottom: 1rem;
}

.board-column {
  width: 300px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  max-height: 100%;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1rem 0.5rem;
  background: white;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid #e1e5e9;
}

.column-title {
  margin: 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.issue-count {
  background: #e9ecef;
  color: #666;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.column-content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: white;
  border-radius: 0 0 8px 8px;
}

/* Issue Cards */
.issue-card {
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.issue-card:hover {
  border-color: #0066cc;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.issue-card.dragging {
  opacity: 0.5;
  transform: rotate(5deg);
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.issue-type {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.type-icon {
  font-size: 0.9rem;
}

.issue-key {
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
}

.issue-priority {
  font-size: 0.9rem;
}

.issue-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
  margin-bottom: 0.75rem;
}

.issue-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.assignee-avatar {
  width: 24px;
  height: 24px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: bold;
}

.issue-points {
  background: #e9ecef;
  color: #666;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.add-issue-btn {
  padding: 0.75rem;
  background: #f8f9fa;
  border: 1px dashed #ddd;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  font-size: 0.9rem;
  transition: all 0.2s;
  margin-top: auto;
}

.add-issue-btn:hover {
  background: #e9ecef;
  border-color: #0066cc;
  color: #0066cc;
}

/* Modal */
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

.issue-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid #e1e5e9;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.3rem;
  line-height: 1.4;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #f8f9fa;
}

.modal-content {
  padding: 1.5rem;
}

.issue-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.detail-row label {
  font-weight: 500;
  color: #666;
  min-width: 100px;
}

.type-badge, .status-badge, .priority-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.type-badge.story { background: #e3f2fd; color: #1976d2; }
.type-badge.bug { background: #ffebee; color: #d32f2f; }
.type-badge.task { background: #e8f5e8; color: #388e3c; }

.status-badge {
  background: #e9ecef;
  color: #495057;
}

.priority-badge.high { background: #ffebee; color: #d32f2f; }
.priority-badge.medium { background: #fff8e1; color: #f57c00; }
.priority-badge.low { background: #e3f2fd; color: #1976d2; }

.assignee-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.unassigned {
  color: #999;
  font-style: italic;
}

.story-points {
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.description-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.description-section label {
  font-weight: 500;
  color: #666;
}

.description-text {
  margin: 0;
  color: #333;
  line-height: 1.5;
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 4px;
}

/* Responsive */
@media (max-width: 768px) {
  .board-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .board-actions {
    justify-content: flex-end;
  }

  .filters-bar {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .board-column {
    width: 280px;
  }
}
</style>