<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

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
                projectData.value.lead.trim()
  
  if (selectedProjectType.value === 'scrum') {
    return basic && projectData.value.startDate
  }
  
  return basic
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

const createProject = async () => {
  if (!isFormValid.value) return
  
  isCreating.value = true
  
  try {
    const payload = {
      ...projectData.value,
      members: selectedMembers.value.map(m => m.id)
    }
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    console.log('Creating project:', payload)
    
    // Redirect to the new project dashboard
    router.push('/dashboard')
    
  } catch (error) {
    console.error('Error creating project:', error)
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

            <div class="form-group">
              <label>Project Lead *</label>
              <input 
                type="text" 
                v-model="projectData.lead"
                placeholder="Enter project lead name or email"
                class="form-input"
              />
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

            <div class="form-group">
              <label>Project Lead *</label>
              <input 
                type="text" 
                v-model="projectData.lead"
                placeholder="Enter project lead name or email"
                class="form-input"
              />
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