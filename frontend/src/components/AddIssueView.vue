<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

const props = defineProps({
  showModal: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'save'])
const reporterId = ref(null)
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const issueTypes = ref([])
const epics = ref([])
const sprints = ref([])
const users = ref([])

// Form data
const formData = ref({
  title: '',
  description: '',
  issue_type: null,
  epic: null,
  sprint: null,
  assignee: null,
  priority: 'medium',
  story_points: null,
  original_estimate: null,
  remaining_estimate: null
})

const priorities = ref([
  { value: 'lowest', label: 'Lowest', color: '#57D9A3' },
  { value: 'low', label: 'Low', color: '#79E2F2' },
  { value: 'medium', label: 'Medium', color: '#FFAB00' },
  { value: 'high', label: 'High', color: '#FF8B00' },
  { value: 'highest', label: 'Highest', color: '#FF5630' }
])

// Validation
const errors = ref({})
const isSubmitting = ref(false)

// Methods
const validateForm = () => {
  errors.value = {}
  
  if (!formData.value.title.trim()) {
    errors.value.title = 'Title is required'
  }
  
  if (!formData.value.issue_type) {
    errors.value.issue_type = 'Issue type is required'
  }
  
  if (formData.value.story_points && (formData.value.story_points < 1 || formData.value.story_points > 100)) {
    errors.value.story_points = 'Story points must be between 1 and 100'
  }
  
  return Object.keys(errors.value).length === 0
}

const resetForm = () => {
  formData.value = {
    title: '',
    description: '',
    issue_type: null,
    epic: null,
    sprint: null,
    assignee: null,
    priority: 'medium',
    story_points: null,
    original_estimate: null,
    remaining_estimate: null
  }
  errors.value = {}
}

const closeModal = () => {
  resetForm()
  emit('close')
}

const saveIssue = async () => {
  if (!validateForm()) return

  isSubmitting.value = true

  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`

    const issueData = {
      ...formData.value,
      project: currentProject.value?.id,
      reporter: reporterId.value
    }

    await axios.post('/api/issues/', issueData)

    emit('save', issueData)
    closeModal()
  } catch (error) {
    console.error('Error saving issue:', error)
  } finally {
    isSubmitting.value = false
  }
}

const getSelectedIssueType = computed(() => {
  return issueTypes.value.find(type => type.id === formData.value.issue_type)
})

const getPriorityColor = (priority) => {
  const priorityObj = priorities.value.find(p => p.value === priority)
  return priorityObj?.color || '#6c757d'
}

const getUserInitials = (user) => {
  return user.name.split(' ').map(n => n[0]).join('')
}

// Convert minutes to hours for display
const minutesToHours = (minutes) => {
  if (!minutes) return ''
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
}

const hoursToMinutes = (hoursString) => {
  if (!hoursString) return null
  // Simple conversion - you might want more sophisticated parsing
  const hours = parseFloat(hoursString)
  return Math.round(hours * 60)
}

onMounted(async () => {
  console.log('AddIssueView mounted, currentProject:', currentProject.value)
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`

  // Fetch current user
  const meRes = await axios.get('/api/me/')
  reporterId.value = meRes.data.id

  // Fetch global issue types
  issueTypes.value = (await axios.get('/api/issue-types/')).data
  if (issueTypes.value.length > 0) {
    formData.value.issue_type = issueTypes.value[0].id
  }
  
  // Fetch issue types for this project
  if (currentProject.value?.id) {
    console.log('Fetching members for project:', currentProject.value.id)
    const pid = currentProject.value.id
    epics.value = (await axios.get(`/api/projects/${pid}/epics/`)).data
    sprints.value = (await axios.get(`/api/projects/${pid}/sprints/`)).data
    users.value = (await axios.get(`/api/projects/${currentProject.value.id}/users/`)).data
    console.log('Fetched project members:', users.value)
  }
})
</script>

<template>
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="issue-modal" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <div>
          <h2>Create Issue</h2>
          <p class="modal-subtitle">Add a new issue to {{ currentProject?.name || 'the project' }}</p>
        </div>
        <button class="close-btn" @click="closeModal">×</button>
      </div>

      <!-- Modal Body -->
      <div class="modal-body">
        <form @submit.prevent="saveIssue">
          <!-- Issue Type Selection -->
          <div class="form-group">
            <label class="form-label required">Issue Type</label>
            <div class="issue-type-grid">
              <div
                v-for="type in issueTypes"
                :key="type.id"
                class="issue-type-option"
                :class="{ active: formData.issue_type === type.id }"
                @click="formData.issue_type = type.id"
              >
                <div class="issue-type-icon" :style="{ backgroundColor: type.color }">
                  {{ type.icon }}
                </div>
                <span class="issue-type-name">{{ type.name }}</span>
              </div>
            </div>
            <div v-if="errors.issue_type" class="error-message">{{ errors.issue_type }}</div>
          </div>

          <!-- Title -->
          <div class="form-group">
            <label class="form-label required">Title</label>
            <input
              v-model="formData.title"
              type="text"
              class="form-input"
              :class="{ error: errors.title }"
              placeholder="Enter issue title"
              maxlength="500"
            />
            <div v-if="errors.title" class="error-message">{{ errors.title }}</div>
          </div>

          <!-- Description -->
          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea
              v-model="formData.description"
              class="form-textarea"
              placeholder="Describe the issue in detail"
              rows="4"
            ></textarea>
          </div>

          <!-- Row: Epic and Sprint -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Epic</label>
              <select v-model="formData.epic" class="form-select">
                <option value="">Unassigned</option>
                <option v-for="epic in epics" :key="epic.id" :value="epic.id">
                  {{ epic.title }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Sprint</label>
              <select v-model="formData.sprint" class="form-select">
                <option value="">Select a sprint</option>
                <option v-for="sprint in sprints" :key="sprint.id" :value="sprint.id">
                  {{ sprint.name }}
                  <span v-if="sprint.status === 'active'">(Active)</span>
                </option>
              </select>
            </div>
          </div>

          <!-- Row: Assignee and Priority -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Assignee</label>
              <select v-model="formData.assignee" class="form-select">
                <option value="">Unassigned</option>
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ user.name }}
                </option>
              </select>
              <div v-if="formData.assignee" class="assignee-preview">
                <div class="assignee-avatar">
                  {{ getUserInitials(users.find(u => u.id === formData.assignee)) }}
                </div>
                <span>{{ users.find(u => u.id === formData.assignee)?.name }}</span>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Priority</label>
              <select v-model="formData.priority" class="form-select">
                <option v-for="priority in priorities" :key="priority.value" :value="priority.value">
                  {{ priority.label }}
                </option>
              </select>
              <div class="priority-preview">
                <span
                  class="priority-badge"
                  :style="{ backgroundColor: getPriorityColor(formData.priority) }"
                >
                  {{ priorities.find(p => p.value === formData.priority)?.label }}
                </span>
              </div>
            </div>
          </div>

          <!-- Row: Story Points and Time Estimates -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Story Points</label>
              <input
                v-model.number="formData.story_points"
                type="number"
                class="form-input"
                :class="{ error: errors.story_points }"
                placeholder="1, 2, 3, 5, 8, 13..."
                min="1"
                max="100"
              />
              <div v-if="errors.story_points" class="error-message">{{ errors.story_points }}</div>
            </div>

            <div class="form-group">
              <label class="form-label">Original Estimate (hours)</label>
              <input
                v-model.number="formData.original_estimate"
                type="number"
                class="form-input"
                placeholder="Hours"
                min="0"
                step="0.5"
              />
            </div>
          </div>

          <!-- Remaining Estimate -->
          <div class="form-group">
            <label class="form-label">Remaining Estimate (hours)</label>
            <input
              v-model.number="formData.remaining_estimate"
              type="number"
              class="form-input"
              placeholder="Hours"
              min="0"
              step="0.5"
            />
          </div>
        </form>
      </div>

      <!-- Modal Footer -->
      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
        <button 
          type="button" 
          class="btn-primary" 
          @click="saveIssue"
          :disabled="isSubmitting"
        >
          <span v-if="isSubmitting">Creating...</span>
          <span v-else>Create Issue</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  overflow-y: auto;
  padding: 2rem;
}

.issue-modal {
  background: white;
  border-radius: 8px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid #e1e5e9;
}

.modal-header h2 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.modal-subtitle {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
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

.modal-body {
  padding: 2rem;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding: 1rem 2rem 2rem;
  border-top: 1px solid #e1e5e9;
}

/* Form Styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-label.required::after {
  content: ' *';
  color: #dc3545;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
}

.form-input.error {
  border-color: #dc3545;
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.error-message {
  color: #dc3545;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

/* Issue Type Selection */
.issue-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.issue-type-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border: 2px solid #e1e5e9;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.issue-type-option:hover {
  border-color: #0066cc;
  background: #f8f9fa;
}

.issue-type-option.active {
  border-color: #0066cc;
  background: #e7f3ff;
}

.issue-type-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
  color: white;
}

.issue-type-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #333;
}

/* Preview Elements */
.assignee-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
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

.priority-preview {
  margin-top: 0.5rem;
}

.priority-badge {
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #0066cc;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

/* Responsive */
@media (max-width: 768px) {
  .modal-overlay {
    padding: 1rem;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .issue-type-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
}
</style>