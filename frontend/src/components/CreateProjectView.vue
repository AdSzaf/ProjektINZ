<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { onMounted } from 'vue'
import { onBeforeUnmount } from 'vue'
import { nextTick } from 'vue'

const router = useRouter()
const users = ref([])
const leadSearch = ref('')
const showLeadDropdown = ref(false)

// Current step in the creation flow
const currentStep = ref('type-selection') // 'type-selection', 'kanban-setup', 'scrum-setup'
const selectedProjectType = ref('')

// Form data
const projectData = ref({
  name: '',
  key: '',
  description: '',
  type: '', // 'kanban' or 'scrum'
  lead: '',
  members: [],
  // Scrum specific
  sprintDuration: 2,
  startDate: '',
  // Kanban specific
  enableWipLimits: false,
  wipLimits: {
    todo: 0,
    inProgress: 3,
    done: 0
  }
})

// Available team members (in real app, fetch from API)
const availableMembers = ref([
  { id: 1, name: 'Alice Johnson', email: 'alice@company.com', avatar: 'AJ', role: 'Developer' },
  { id: 2, name: 'Bob Smith', email: 'bob@company.com', avatar: 'BS', role: 'Designer' },
  { id: 3, name: 'Charlie Brown', email: 'charlie@company.com', avatar: 'CB', role: 'Product Manager' },
  { id: 4, name: 'Diana Prince', email: 'diana@company.com', avatar: 'DP', role: 'QA Engineer' },
  { id: 5, name: 'Eve Wilson', email: 'eve@company.com', avatar: 'EW', role: 'Developer' }
])

const selectedMembers = ref([])
const showMemberDropdown = ref(false)
const isCreating = ref(false)
const searchInput = ref(null)

// Computed properties
const projectKeyPreview = computed(() => {
  if (!projectData.value.name) return ''
  return projectData.value.name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .join('')
    .substring(0, 4)
})

const isFormValid = computed(() => {
  const basic = projectData.value.name.trim() &&
                projectData.value.description.trim() &&
                projectData.value.lead // just check for presence, not .trim()
  if (selectedProjectType.value === 'scrum') {
    return basic && projectData.value.startDate
  }
  return basic
})

const filteredUsers = computed(() => {
  if (!leadSearch.value) return users.value
  return users.value.filter(u =>
    (u.first_name + ' ' + u.last_name + ' ' + u.email)
      .toLowerCase()
      .includes(leadSearch.value.toLowerCase())
  )
})

// Methods
const selectProjectType = (type) => {
  selectedProjectType.value = type
  projectData.value.type = type
  currentStep.value = type === 'kanban' ? 'kanban-setup' : 'scrum-setup'
}

const goBack = () => {
  if (currentStep.value === 'kanban-setup' || currentStep.value === 'scrum-setup') {
    currentStep.value = 'type-selection'
    selectedProjectType.value = ''
  } else {
    router.push('/dashboard')
  }
}

const toggleMember = (member) => {
  const index = selectedMembers.value.findIndex(m => m.id === member.id)
  if (index > -1) {
    selectedMembers.value.splice(index, 1)
  } else {
    selectedMembers.value.push(member)
  }
}

const removeMember = (memberId) => {
  selectedMembers.value = selectedMembers.value.filter(m => m.id !== memberId)
}

const updateProjectKey = () => {
  if (!projectData.value.key) {
    projectData.value.key = projectKeyPreview.value
  }
}

const openLeadDropdown = () => {
  showLeadDropdown.value = true
  nextTick(() => {
    if (searchInput.value) {
      searchInput.value.focus()
    }
  })
}

const selectLead = (user) => {
  projectData.value.lead = user.id
  projectData.value.leadName = `${user.first_name} ${user.last_name}`
  showLeadDropdown.value = false
  leadSearch.value = ''
}

const createProject = async () => {
  if (!isFormValid.value) return

  isCreating.value = true

  try {
    // Fetch current user info if needed
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`

    // Optionally fetch user/org info if not already set
    if (!projectData.value.lead || !projectData.value.organization) {
      const res = await axios.get('/api/me/')
      if (!projectData.value.lead) projectData.value.lead = res.data.id
      if (!projectData.value.organization && res.data.organizations?.length) {
        // If user has multiple orgs, pick the first for now
        projectData.value.organization = res.data.organizations[0].id
      }
    }

    // Prepare payload for backend
    const payload = {
      name: projectData.value.name,
      key: projectData.value.key,
      description: projectData.value.description,
      methodology: projectData.value.type, // 'scrum' or 'kanban'
      lead: projectData.value.lead,
      organization: projectData.value.organization,
      // You can add more fields as your backend supports them
    }

    const response = await axios.post('/api/projects/', payload)
    // Optionally show a success message
    router.push('/dashboard')
  } catch (error) {
    console.error('Error creating project:', error)
    alert('Failed to create project: ' + (error.response?.data?.detail || error.message))
  } finally {
    isCreating.value = false
  }
}

// Set default start date for scrum projects
const setDefaultStartDate = () => {
  const today = new Date()
  const nextMonday = new Date(today)
  nextMonday.setDate(today.getDate() + (1 + 7 - today.getDay()) % 7)
  projectData.value.startDate = nextMonday.toISOString().split('T')[0]
}

// Initialize default values when scrum is selected
const initializeScrumDefaults = () => {
  if (!projectData.value.startDate) {
    setDefaultStartDate()
  }
}

const handleClickOutside = (event) => {
  const leadSelector = event.target.closest('.lead-selector')
  if (!leadSelector) {
    showLeadDropdown.value = false
  }
  
  const memberSelector = event.target.closest('.member-selector')
  if (!memberSelector) {
    showMemberDropdown.value = false
  }
}

onMounted(async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  try {
    const res = await axios.get('/api/me/')
    projectData.value.lead = res.data.id
    projectData.value.leadName = `${res.data.first_name} ${res.data.last_name}`
    if (res.data.organizations?.length) {
      projectData.value.organization = res.data.organizations[0].id
    }
    // Fetch all users for dropdown
    const usersRes = await axios.get('/api/users/')
    users.value = usersRes.data
  } catch (e) {
    if (e.response && e.response.status === 401) {
      alert('Session expired. Please log in again.')
      router.push('/login')
    } else {
      alert('Could not fetch user info. Please try again later.')
    }
  }
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

</script>

<template>
  <div class="project-creation">
    <!-- Header -->
    <div class="creation-header">
      <button class="back-btn" @click="goBack">
        ← Back
      </button>
      <div class="header-content">
        <h1>Create New Project</h1>
        <div class="step-indicator">
          <div class="step" :class="{ active: currentStep === 'type-selection' }">
            1. Choose Type
          </div>
          <div class="step" :class="{ active: currentStep === 'kanban-setup' || currentStep === 'scrum-setup' }">
            2. Project Setup
          </div>
        </div>
      </div>
    </div>

    <!-- Project Type Selection -->
    <div v-if="currentStep === 'type-selection'" class="type-selection">
      <div class="type-cards">
        <div 
          class="type-card" 
          :class="{ selected: selectedProjectType === 'kanban' }"
          @click="selectProjectType('kanban')"
        >
          <div class="type-icon">📋</div>
          <h3>Kanban Project</h3>
          <p>Visualize and advance your work through a continuous flow</p>
          <ul class="type-features">
            <li>Continuous workflow</li>
            <li>WIP limits</li>
            <li>Flexible priorities</li>
            <li>Real-time collaboration</li>
          </ul>
        </div>

        <div 
          class="type-card" 
          :class="{ selected: selectedProjectType === 'scrum' }"
          @click="selectProjectType('scrum')"
        >
          <div class="type-icon">🏃</div>
          <h3>Scrum Project</h3>
          <p>Work in sprints and deliver value incrementally</p>
          <ul class="type-features">
            <li>Time-boxed sprints</li>
            <li>Sprint planning</li>
            <li>Burndown charts</li>
            <li>Retrospectives</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Kanban Project Setup -->
    <div v-if="currentStep === 'kanban-setup'" class="project-setup kanban-setup">
      <div class="setup-container">
        <div class="setup-main">
          <div class="form-section">
            <h2>📋 Kanban Project Details</h2>
            
            <div class="form-group">
              <label>Project Name *</label>
              <input 
                type="text" 
                v-model="projectData.name"
                @input="updateProjectKey"
                placeholder="Enter project name"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label>Project Key *</label>
              <input 
                type="text" 
                v-model="projectData.key"
                :placeholder="projectKeyPreview || 'AUTO'"
                class="form-input key-input"
                maxlength="10"
              />
              <small class="form-hint">This will be used as prefix for issue keys (e.g., PROJ-123)</small>
            </div>

            <div class="form-group">
              <label>Description *</label>
              <textarea 
                v-model="projectData.description"
                placeholder="Describe your project's purpose and goals"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>

            <div class="form-group lead-selector">
              <label>Project Lead *</label>
              <div class="lead-input-container" :class="{ open: showLeadDropdown }">
                <input
                  type="text"
                  v-model="projectData.leadName"
                  @focus="showLeadDropdown = true"
                  @click="showLeadDropdown = true"
                  placeholder="Select project lead"
                  class="form-input lead-input"
                  autocomplete="off"
                  readonly
                />
                
                <div v-if="showLeadDropdown" class="dropdown lead-dropdown">
                  <input
                    type="text"
                    v-model="leadSearch"
                    placeholder="Search users by name or email..."
                    class="dropdown-search"
                    @input="showLeadDropdown = true"
                    ref="searchInput"
                  />
                  
                  <div class="dropdown-items">
                    <div
                      v-for="user in filteredUsers"
                      :key="user.id"
                      class="dropdown-item"
                      :class="{ selected: projectData.lead === user.id }"
                      @mousedown.prevent="selectLead(user)"
                      tabindex="0"
                      @keydown.enter="selectLead(user)"
                      @keydown.space.prevent="selectLead(user)"
                    >
                      <div class="user-avatar">
                        {{ (user.first_name?.charAt(0) || '') + (user.last_name?.charAt(0) || '') }}
                      </div>
                      <div class="user-info">
                        <div class="user-name">{{ user.first_name }} {{ user.last_name }}</div>
                        <div class="user-email">{{ user.email }}</div>
                      </div>
                    </div>
                    
                    <div v-if="filteredUsers.length === 0" class="dropdown-no-results">
                      No users found matching "{{ leadSearch }}"
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Kanban Specific Settings -->
            <div class="kanban-settings">
              <h3>Kanban Configuration</h3>
              
              <div class="form-group">
                <label class="checkbox-label">
                  <input 
                    type="checkbox" 
                    v-model="projectData.enableWipLimits"
                    class="form-checkbox"
                  />
                  Enable WIP (Work In Progress) Limits
                </label>
                <small class="form-hint">Limit the number of items in each column to improve flow</small>
              </div>

              <div v-if="projectData.enableWipLimits" class="wip-limits">
                <div class="wip-grid">
                  <div class="wip-item">
                    <label>To Do</label>
                    <input 
                      type="number" 
                      v-model="projectData.wipLimits.todo"
                      min="0"
                      class="form-input wip-input"
                      placeholder="0 = No limit"
                    />
                  </div>
                  <div class="wip-item">
                    <label>In Progress</label>
                    <input 
                      type="number" 
                      v-model="projectData.wipLimits.inProgress"
                      min="1"
                      class="form-input wip-input"
                    />
                  </div>
                  <div class="wip-item">
                    <label>Done</label>
                    <input 
                      type="number" 
                      v-model="projectData.wipLimits.done"
                      min="0"
                      class="form-input wip-input"
                      placeholder="0 = No limit"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="setup-sidebar">
          <div class="sidebar-section">
            <h3>👥 Team Members</h3>
            <p class="section-description">Add team members to your project</p>
            
            <div class="member-selector" @click.stop>
              <button 
                class="add-member-btn"
                @click="showMemberDropdown = !showMemberDropdown"
              >
                + Add Members
              </button>
              
              <div v-if="showMemberDropdown" class="member-dropdown">
                <div 
                  v-for="member in availableMembers" 
                  :key="member.id"
                  class="member-option"
                  @click="toggleMember(member)"
                >
                  <div class="member-info">
                    <div class="member-avatar">{{ member.avatar }}</div>
                    <div>
                      <div class="member-name">{{ member.name }}</div>
                      <div class="member-role">{{ member.role }}</div>
                    </div>
                  </div>
                  <div class="member-checkbox">
                    <input 
                      type="checkbox" 
                      :checked="selectedMembers.some(m => m.id === member.id)"
                      readonly
                    />
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedMembers.length > 0" class="selected-members">
              <div 
                v-for="member in selectedMembers" 
                :key="member.id"
                class="selected-member"
              >
                <div class="member-avatar">{{ member.avatar }}</div>
                <div class="member-details">
                  <div class="member-name">{{ member.name }}</div>
                  <div class="member-role">{{ member.role }}</div>
                </div>
                <button 
                  class="remove-btn"
                  @click="removeMember(member.id)"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn btn-secondary" @click="goBack">
          Back
        </button>
        <button 
          class="btn btn-primary" 
          @click="createProject"
          :disabled="!isFormValid || isCreating"
        >
          <span v-if="isCreating">Creating...</span>
          <span v-else>Create Kanban Project</span>
        </button>
      </div>
    </div>

    <!-- Scrum Project Setup -->
    <div v-if="currentStep === 'scrum-setup'" class="project-setup scrum-setup">
      <div class="setup-container">
        <div class="setup-main">
          <div class="form-section">
            <h2>🏃 Scrum Project Details</h2>
            
            <div class="form-group">
              <label>Project Name *</label>
              <input 
                type="text" 
                v-model="projectData.name"
                @input="updateProjectKey"
                placeholder="Enter project name"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label>Project Key *</label>
              <input 
                type="text" 
                v-model="projectData.key"
                :placeholder="projectKeyPreview || 'AUTO'"
                class="form-input key-input"
                maxlength="10"
              />
              <small class="form-hint">This will be used as prefix for issue keys (e.g., PROJ-123)</small>
            </div>

            <div class="form-group">
              <label>Description *</label>
              <textarea 
                v-model="projectData.description"
                placeholder="Describe your project's purpose and goals"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>

           <div class="form-group lead-selector">
              <label>Project Lead *</label>
              <div class="lead-input-container" :class="{ open: showLeadDropdown }">
                <input
                  type="text"
                  v-model="projectData.leadName"
                  @focus="showLeadDropdown = true"
                  @click="showLeadDropdown = true"
                  placeholder="Select project lead"
                  class="form-input lead-input"
                  autocomplete="off"
                  readonly
                />
                
                <div v-if="showLeadDropdown" class="dropdown lead-dropdown">
                  <input
                    type="text"
                    v-model="leadSearch"
                    placeholder="Search users by name or email..."
                    class="dropdown-search"
                    @input="showLeadDropdown = true"
                    ref="searchInput"
                  />
                  
                  <div class="dropdown-items">
                    <div
                      v-for="user in filteredUsers"
                      :key="user.id"
                      class="dropdown-item"
                      :class="{ selected: projectData.lead === user.id }"
                      @mousedown.prevent="selectLead(user)"
                      tabindex="0"
                      @keydown.enter="selectLead(user)"
                      @keydown.space.prevent="selectLead(user)"
                    >
                      <div class="user-avatar">
                        {{ (user.first_name?.charAt(0) || '') + (user.last_name?.charAt(0) || '') }}
                      </div>
                      <div class="user-info">
                        <div class="user-name">{{ user.first_name }} {{ user.last_name }}</div>
                        <div class="user-email">{{ user.email }}</div>
                      </div>
                    </div>
                    
                    <div v-if="filteredUsers.length === 0" class="dropdown-no-results">
                      No users found matching "{{ leadSearch }}"
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Scrum Specific Settings -->
            <div class="scrum-settings">
              <h3>Scrum Configuration</h3>
              
              <div class="form-row">
                <div class="form-group">
                  <label>Sprint Duration</label>
                  <select v-model="projectData.sprintDuration" class="form-select">
                    <option value="1">1 week</option>
                    <option value="2">2 weeks</option>
                    <option value="3">3 weeks</option>
                    <option value="4">4 weeks</option>
                  </select>
                </div>

                <div class="form-group">
                  <label>First Sprint Start Date *</label>
                  <input 
                    type="date" 
                    v-model="projectData.startDate"
                    class="form-input"
                    @focus="initializeScrumDefaults"
                  />
                </div>
              </div>

              <div class="sprint-info">
                <div class="info-card">
                  <h4>📅 Sprint Schedule</h4>
                  <p>Your sprints will run for {{ projectData.sprintDuration }} week{{ projectData.sprintDuration > 1 ? 's' : '' }} each</p>
                  <p v-if="projectData.startDate">First sprint starts: {{ new Date(projectData.startDate).toLocaleDateString() }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="setup-sidebar">
          <div class="sidebar-section">
            <h3>👥 Team Members</h3>
            <p class="section-description">Add team members to your project</p>
            
            <div class="member-selector" @click.stop>
              <button 
                class="add-member-btn"
                @click="showMemberDropdown = !showMemberDropdown"
              >
                + Add Members
              </button>
              
              <div v-if="showMemberDropdown" class="member-dropdown">
                <div 
                  v-for="member in availableMembers" 
                  :key="member.id"
                  class="member-option"
                  @click="toggleMember(member)"
                >
                  <div class="member-info">
                    <div class="member-avatar">{{ member.avatar }}</div>
                    <div>
                      <div class="member-name">{{ member.name }}</div>
                      <div class="member-role">{{ member.role }}</div>
                    </div>
                  </div>
                  <div class="member-checkbox">
                    <input 
                      type="checkbox" 
                      :checked="selectedMembers.some(m => m.id === member.id)"
                      readonly
                    />
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedMembers.length > 0" class="selected-members">
              <div 
                v-for="member in selectedMembers" 
                :key="member.id"
                class="selected-member"
              >
                <div class="member-avatar">{{ member.avatar }}</div>
                <div class="member-details">
                  <div class="member-name">{{ member.name }}</div>
                  <div class="member-role">{{ member.role }}</div>
                </div>
                <button 
                  class="remove-btn"
                  @click="removeMember(member.id)"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn btn-secondary" @click="goBack">
          Back
        </button>
        <button 
          class="btn btn-primary" 
          @click="createProject"
          :disabled="!isFormValid || isCreating"
        >
          <span v-if="isCreating">Creating...</span>
          <span v-else>Create Scrum Project</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-creation {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.creation-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
}

.back-btn:hover {
  background: #e9ecef;
  border-color: #0066cc;
  color: #0066cc;
}

.header-content h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.step-indicator {
  display: flex;
  gap: 1rem;
}

.step {
  padding: 0.25rem 0.75rem;
  background: #e9ecef;
  border-radius: 20px;
  font-size: 0.9rem;
  color: #666;
  transition: all 0.2s;
}

.step.active {
  background: #0066cc;
  color: white;
}

/* Type Selection */
.type-selection {
  max-width: 800px;
  margin: 0 auto;
}

.type-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.type-card {
  background: white;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.type-card:hover {
  border-color: #0066cc;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1);
}

.type-card.selected {
  border-color: #0066cc;
  background: #f8fbff;
}

.type-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.type-card h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.type-card p {
  color: #666;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.type-features {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}

.type-features li {
  padding: 0.5rem 0;
  color: #666;
  position: relative;
  padding-left: 1.5rem;
}

.type-features li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #28a745;
  font-weight: bold;
}

/* Project Setup */
.setup-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.setup-main {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.setup-sidebar {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.form-section h2 {
  margin: 0 0 2rem 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-input, .form-textarea, .form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus, .form-textarea:focus, .form-select:focus {
  outline: none;
  border-color: #0066cc;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.key-input {
  text-transform: uppercase;
  font-family: monospace;
}

.form-hint {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.9rem;
  color: #666;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Kanban Settings */
.kanban-settings, .scrum-settings {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e1e5e9;
}

.kanban-settings h3, .scrum-settings h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.form-checkbox {
  width: auto;
}

.wip-limits {
  margin-top: 1rem;
}

.wip-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
}

.wip-item label {
  font-size: 0.9rem;
  color: #666;
}

.wip-input {
  margin-top: 0.25rem;
}

/* Sprint Info */
.sprint-info {
  margin-top: 1.5rem;
}

.info-card {
  background: #f8fbff;
  border: 1px solid #e3f2fd;
  border-radius: 4px;
  padding: 1rem;
}

.info-card h4 {
  margin: 0 0 0.5rem 0;
  color: #0066cc;
  font-size: 1rem;
}

.info-card p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}

/* Sidebar */
.sidebar-section {
  margin-bottom: 2rem;
}

.sidebar-section h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.member-selector {
  position: relative;
}

.add-member-btn {
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.75rem 1rem;
  cursor: pointer;
  width: 100%;
  transition: all 0.2s;
  color: #0066cc;
  font-weight: 500;
}

.add-member-btn:hover {
  background: #e9ecef;
  border-color: #0066cc;
}

.member-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 0.25rem;
}

.member-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.member-option:hover {
  background: #f8f9fa;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.member-avatar {
  width: 32px;
  height: 32px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.member-name {
  font-weight: 500;
  color: #333;
}

.member-role {
  font-size: 0.9rem;
  color: #666;
}

.selected-members {
  margin-top: 1rem;
}

.selected-member {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fbff;
  border: 1px solid #e3f2fd;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.member-details {
  flex: 1;
}

.remove-btn {
  background: none;
  border: none;
  color: #e74c3c;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 2rem auto 0;
  padding-top: 2rem;
  border-top: 1px solid #e1e5e9;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  font-size: 1rem;
}

.btn-secondary {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e9ecef;
  border-color: #ccc;
}

.btn-primary {
  background: #0066cc;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.form-input.lead-input {
  background: var(--bg-color, #fff);
  color: var(--text-color, #333);
  border: 2px solid var(--border-color, #ddd);
  cursor: pointer;
  position: relative;
}

.form-input.lead-input:focus {
  border-color: var(--primary-color, #0066cc);
  box-shadow: 0 0 0 3px var(--primary-color-alpha, rgba(0, 102, 204, 0.1));
}

.lead-input-container {
  position: relative;
}

.lead-input-container::after {
  content: '▼';
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted, #666);
  pointer-events: none;
  transition: transform 0.2s ease;
  font-size: 0.8rem;
}

.lead-input-container.open::after {
  transform: translateY(-50%) rotate(180deg);
}

/* Main dropdown container */
.dropdown.lead-dropdown {
  position: absolute;
  top: calc(100% + 0.25rem);
  left: 0;
  width: 100%;           
  background: var(--dropdown-bg, #fff);
  border: 2px solid var(--primary-color, #0066cc);
  border-radius: 8px;
  box-shadow: 0 8px 24px var(--shadow-color, rgba(0, 0, 0, 0.15));
  z-index: 1000;
  max-height: 320px;
  overflow: hidden;
  animation: dropdownSlideIn 0.2s ease-out;
}

@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Search input within dropdown */
.lead-dropdown .dropdown-search {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-bottom: 1px solid var(--border-light, #e9ecef);
  background: var(--search-bg, #f8f9fa);
  color: var(--text-color, #333);
  font-size: 0.95rem;
  outline: none;
  border-radius: 6px 6px 0 0;
}

.lead-dropdown .dropdown-search:focus {
  background: var(--search-focus-bg, #fff);
  border-bottom-color: var(--primary-color, #0066cc);
}

.lead-dropdown .dropdown-search::placeholder {
  color: var(--text-muted, #999);
}

/* Dropdown items container */
.dropdown-items {
  max-height: 240px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb, #ccc) var(--scrollbar-track, #f1f1f1);
}

.dropdown-items::-webkit-scrollbar {
  width: 6px;
}

.dropdown-items::-webkit-scrollbar-track {
  background: var(--scrollbar-track, #f1f1f1);
}

.dropdown-items::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb, #ccc);
  border-radius: 3px;
}

.dropdown-items::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover, #999);
}

/* Individual dropdown items */
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid var(--border-light, #f0f0f0);
  background: var(--item-bg, transparent);
  color: var(--text-color, #333);
}

.dropdown-item:hover {
  background: var(--item-hover-bg, #f8fbff);
  border-left: 3px solid var(--primary-color, #0066cc);
  padding-left: calc(1rem - 3px);
}

.dropdown-item:last-child {
  border-bottom: none;
}

/* User avatar in dropdown */
.dropdown-item .user-avatar {
  width: 36px;
  height: 36px;
  background: var(--avatar-bg, #0066cc);
  color: var(--avatar-text, #fff);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  flex-shrink: 0;
  border: 2px solid var(--avatar-border, transparent);
}

/* User info in dropdown */
.dropdown-item .user-info {
  flex: 1;
  min-width: 0;
}

.dropdown-item .user-name {
  font-weight: 500;
  color: var(--text-color, #333);
  margin-bottom: 0.125rem;
  font-size: 0.95rem;
}

.dropdown-item .user-email {
  color: var(--text-muted, #666);
  font-size: 0.85rem;
  opacity: 0.9;
}

/* No results state */
.dropdown-no-results {
  padding: 1.5rem 1rem;
  text-align: center;
  color: var(--text-muted, #999);
  font-style: italic;
}

.dropdown-no-results::before {
  content: '🔍';
  display: block;
  font-size: 2rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

/* Loading state */
.dropdown-loading {
  padding: 1.5rem 1rem;
  text-align: center;
  color: var(--text-muted, #666);
}

.dropdown-loading::before {
  content: '';
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color, #ddd);
  border-top-color: var(--primary-color, #0066cc);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Selected state indicator */
.dropdown-item.selected {
  background: var(--selected-bg, #e8f4fd);
  border-left: 3px solid var(--primary-color, #0066cc);
  padding-left: calc(1rem - 3px);
}

.dropdown-item.selected .user-avatar {
  border-color: var(--primary-color, #0066cc);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .dropdown.lead-dropdown {
    --dropdown-bg: #2d3748;
    --border-color: #4a5568;
    --border-light: #4a5568;
    --text-color: #e2e8f0;
    --text-muted: #a0aec0;
    --search-bg: #4a5568;
    --search-focus-bg: #2d3748;
    --item-bg: transparent;
    --item-hover-bg: #4a5568;
    --selected-bg: #2b6cb0;
    --avatar-bg: #3182ce;
    --avatar-text: #fff;
    --avatar-border: transparent;
    --shadow-color: rgba(0, 0, 0, 0.3);
    --scrollbar-track: #4a5568;
    --scrollbar-thumb: #718096;
    --scrollbar-thumb-hover: #a0aec0;
  }

  .form-input.lead-input {
    --bg-color: #2d3748;
    --text-color: #e2e8f0;
    --border-color: #4a5568;
  }

  .lead-input-container::after {
    --text-muted: #a0aec0;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .dropdown.lead-dropdown {
    border-width: 3px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .dropdown-item:hover {
    border-left-width: 4px;
  }

  .dropdown-item.selected {
    border-left-width: 4px;
  }
}

/* Focus management for accessibility */
.dropdown-item:focus {
  outline: 2px solid var(--primary-color, #0066cc);
  outline-offset: -2px;
  background: var(--item-hover-bg, #f8fbff);
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .dropdown.lead-dropdown {
    animation: none;
  }

  .lead-input-container::after {
    transition: none;
  }

  .dropdown-item {
    transition: none;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .type-cards {
    grid-template-columns: 1fr;
  }
  
  .setup-container {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .wip-grid {
    grid-template-columns: 1fr;
  }
  
  .creation-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .step-indicator {
    order: -1;
  }
  
  .project-creation {
    padding: 1rem;
  }
  
  .setup-main, .setup-sidebar {
    padding: 1.5rem;
  }
  
  .form-actions {
    flex-direction: column;
    gap: 1rem;
  }
  
  .form-actions .btn {
    width: 100%;
  }

  .dropdown.lead-dropdown {
    max-height: 50vh;
    border-radius: 12px;
    margin-top: 0.5rem;
  }

  .dropdown-item {
    padding: 1rem;
  }

  .dropdown-item .user-avatar {
    width: 32px;
    height: 32px;
  }

  .lead-dropdown .dropdown-search {
    padding: 1rem;
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .type-card {
    padding: 1.5rem;
  }
  
  .type-icon {
    font-size: 2rem;
  }
}
</style>