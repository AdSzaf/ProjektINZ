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
        <button class="btn btn-primary" @click="createIssue">
          + Create Issue
        </button>
      </div>
    </div>

    <div class="backlog-filters">
      <div class="filter-group">
        <select v-model="selectedEpic" class="filter-select">
          <option value="">All Epics</option>
          <option v-for="epic in epics" :key="epic.id" :value="epic.id">
            {{ epic.name }}
          </option>
        </select>
        
        <select v-model="selectedAssignee" class="filter-select">
          <option value="">All Assignees</option>
          <option v-for="member in teamMembers" :key="member.id" :value="member.id">
            {{ member.name }}
          </option>
        </select>

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
      <div class="sprint-planning" v-if="futureSprints.length > 0">
        <h3>Sprint Planning</h3>
        <div 
          v-for="sprint in futureSprints" 
          :key="sprint.id"
          class="sprint-container"
          @drop="onDrop($event, sprint.id)"
          @dragover.prevent
          @dragenter.prevent
        >
          <div class="sprint-header">
            <div class="sprint-info">
              <span class="sprint-name">{{ sprint.name }}</span>
              <span class="sprint-dates">{{ sprint.startDate }} - {{ sprint.endDate }}</span>
              <span class="sprint-capacity">{{ sprint.issues.length }}/{{ sprint.capacity }} issues</span>
            </div>
            <div class="sprint-actions">
              <button class="btn-icon" @click="startSprint(sprint.id)">▶️</button>
              <button class="btn-icon" @click="editSprint(sprint.id)">✏️</button>
            </div>
          </div>
          
          <div class="sprint-issues" :class="{ empty: sprint.issues.length === 0 }">
            <div 
              v-for="issue in sprint.issues" 
              :key="issue.id"
              class="issue-card"
              :class="{ selected: selectedIssues.includes(issue.id) }"
              draggable="true"
              @dragstart="onDragStart($event, issue)"
              @click="selectIssue(issue.id)"
            >
              <div class="issue-header">
                <span class="issue-key">{{ issue.key }}</span>
                <span class="issue-type">{{ getIssueTypeIcon(issue.type) }}</span>
                <span class="issue-priority">{{ getPriorityIcon(issue.priority) }}</span>
              </div>
              <div class="issue-title">{{ issue.title }}</div>
              <div class="issue-meta">
                <span class="issue-assignee" v-if="issue.assignee">
                  {{ issue.assignee.initials }}
                </span>
                <span class="issue-story-points" v-if="issue.storyPoints">
                  {{ issue.storyPoints }}
                </span>
              </div>
            </div>
            <div v-if="sprint.issues.length === 0" class="empty-sprint">
              Drop issues here to add to {{ sprint.name }}
            </div>
          </div>
        </div>
      </div>

      <!-- Product Backlog -->
      <div class="product-backlog">
        <div class="backlog-header">
          <h3>Product Backlog</h3>
          <div class="backlog-stats">
            <span>{{ filteredBacklogIssues.length }} issues</span>
            <span>{{ totalStoryPoints }} story points</span>
          </div>
        </div>

        <div 
          class="backlog-issues"
          @drop="onDrop($event, 'backlog')"
          @dragover.prevent
          @dragenter.prevent
        >
          <div 
            v-for="issue in filteredBacklogIssues" 
            :key="issue.id"
            class="issue-card"
            :class="{ 
              selected: selectedIssues.includes(issue.id),
              detailed: viewMode === 'detailed'
            }"
            draggable="true"
            @dragstart="onDragStart($event, issue)"
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
                <span class="issue-type">{{ getIssueTypeIcon(issue.type) }}</span>
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
                  {{ issue.assignee.initials }}
                </span>
                <span class="issue-story-points" v-if="issue.storyPoints">
                  {{ issue.storyPoints }} SP
                </span>
                <span class="issue-status">{{ issue.status }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Data
const bulkEditMode = ref(false)
const selectedIssues = ref([])
const viewMode = ref('list')
const selectedEpic = ref('')
const selectedAssignee = ref('')
const searchQuery = ref('')

const epics = ref([
  { id: 1, name: 'User Authentication', key: 'AUTH' },
  { id: 2, name: 'Dashboard Redesign', key: 'DASH' },
  { id: 3, name: 'Mobile Support', key: 'MOB' }
])

const teamMembers = ref([
  { id: 1, name: 'Alice Johnson', initials: 'AJ' },
  { id: 2, name: 'Bob Smith', initials: 'BS' },
  { id: 3, name: 'Charlie Brown', initials: 'CB' },
  { id: 4, name: 'Diana Prince', initials: 'DP' }
])

const futureSprints = ref([
  {
    id: 1,
    name: 'Sprint 24',
    startDate: '2025-08-01',
    endDate: '2025-08-14',
    capacity: 25,
    issues: [
      {
        id: 101,
        key: 'AP-101',
        title: 'Implement OAuth login',
        type: 'story',
        priority: 'high',
        assignee: { name: 'Alice Johnson', initials: 'AJ' },
        storyPoints: 8,
        epic: { name: 'User Authentication', key: 'AUTH' },
        status: 'To Do'
      }
    ]
  }
])

const backlogIssues = ref([
  {
    id: 1,
    key: 'AP-147',
    title: 'Create user profile management',
    description: 'Allow users to edit their profile information including avatar, personal details, and preferences.',
    type: 'story',
    priority: 'high',
    assignee: { name: 'Alice Johnson', initials: 'AJ' },
    storyPoints: 5,
    epic: { name: 'User Authentication', key: 'AUTH' },
    status: 'To Do'
  },
  {
    id: 2,
    key: 'AP-148',
    title: 'Add dark mode toggle',
    description: 'Implement system-wide dark mode with user preference persistence.',
    type: 'story',
    priority: 'medium',
    assignee: { name: 'Bob Smith', initials: 'BS' },
    storyPoints: 3,
    epic: { name: 'Dashboard Redesign', key: 'DASH' },
    status: 'To Do'
  },
  {
    id: 3,
    key: 'AP-149',
    title: 'Fix mobile responsiveness issues',
    description: 'Address layout issues on mobile devices for better user experience.',
    type: 'bug',
    priority: 'high',
    assignee: { name: 'Charlie Brown', initials: 'CB' },
    storyPoints: 2,
    epic: { name: 'Mobile Support', key: 'MOB' },
    status: 'To Do'
  },
  {
    id: 4,
    key: 'AP-150',
    title: 'Implement search functionality',
    description: 'Add global search across issues, epics, and sprints with advanced filters.',
    type: 'story',
    priority: 'medium',
    assignee: null,
    storyPoints: 8,
    epic: null,
    status: 'To Do'
  },
  {
    id: 5,
    key: 'AP-151',
    title: 'Add export functionality',
    description: 'Allow users to export project data in various formats (CSV, PDF, Excel).',
    type: 'feature',
    priority: 'low',
    assignee: { name: 'Diana Prince', initials: 'DP' },
    storyPoints: 5,
    epic: null,
    status: 'To Do'
  }
])

// Computed properties
const filteredBacklogIssues = computed(() => {
  let filtered = backlogIssues.value

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

const startSprint = (sprintId) => {
  console.log('Start sprint:', sprintId)
}

const editSprint = (sprintId) => {
  console.log('Edit sprint:', sprintId)
}

const onDragStart = (event, issue) => {
  event.dataTransfer.setData('text/plain', JSON.stringify(issue))
}

const onDrop = (event, target) => {
  const issueData = JSON.parse(event.dataTransfer.getData('text/plain'))
  console.log('Drop issue', issueData.id, 'to', target)
  // Handle issue movement logic here
}

const getIssueTypeIcon = (type) => {
  const icons = {
    story: '📝',
    bug: '🐛',
    feature: '⭐',
    task: '✅',
    epic: '📚'
  }
  return icons[type] || '📝'
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
</script>

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
  padding: 0.2rem 0.4rem;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: bold;
  min-width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
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
</style>