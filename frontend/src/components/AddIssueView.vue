<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

const props = defineProps({
  showModal: {
    type: Boolean,
    default: false
  },
  mode: { type: String, default: 'add' }, // 'add' or 'edit'
  issue: { type: Object, default: null }
})

const emit = defineEmits(['close', 'save'])
const reporterId = ref(null)
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const issueTypes = ref([])
const epics = ref([])
const sprints = ref([])
const users = ref([])

// Tags functionality
const availableTags = ref([])
const selectedTags = ref([])
const showTagDropdown = ref(false)
const newTagName = ref('')
const showNewTagInput = ref(false)
const tagColors = [
  '#FF5630', '#FF8B00', '#FFAB00', '#36B37E', 
  '#00B8D9', '#6554C0', '#FF5630', '#97A0AF'
]

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

// Tag methods
const fetchTags = async () => {
  if (!currentProject.value?.id) return
  try {
    const response = await axios.get(`/api/projects/${currentProject.value.id}/tags/`)
    availableTags.value = response.data
  } catch (error) {
    console.error('Error fetching tags:', error)
  }
}

const createTag = async () => {
  if (!newTagName.value.trim()) return
  
  try {
    const randomColor = tagColors[Math.floor(Math.random() * tagColors.length)]
    const response = await axios.post(`/api/projects/${currentProject.value.id}/tags/`, {
      name: newTagName.value.trim(),
      color: randomColor
    })
    
    const newTag = response.data
    availableTags.value.push(newTag)
    selectedTags.value.push(newTag)
    
    newTagName.value = ''
    showNewTagInput.value = false
  } catch (error) {
    console.error('Error creating tag:', error)
  }
}

const toggleTag = (tag) => {
  const index = selectedTags.value.findIndex(t => t.id === tag.id)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

const removeTag = (tagId) => {
  selectedTags.value = selectedTags.value.filter(t => t.id !== tagId)
}

const isTagSelected = (tag) => {
  return selectedTags.value.some(t => t.id === tag.id)
}

const filteredTags = computed(() => {
  return availableTags.value.filter(tag => !isTagSelected(tag))
})

const updateIssue = async () => {
  if (!validateForm()) return
  isSubmitting.value = true
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    
    const updateData = {
      ...formData.value,
      tags: selectedTags.value.map(tag => tag.id)
    }
    
    await axios.patch(`/api/issues/${props.issue.id}/`, updateData)
    emit('save', updateData)
    closeModal()
  } catch (error) {
    console.error('Error updating issue:', error)
  } finally {
    isSubmitting.value = false
  }
}

const errors = ref({})
const isSubmitting = ref(false)

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
  selectedTags.value = []
  errors.value = {}
}

const closeModal = () => {
  resetForm()
  showTagDropdown.value = false
  showNewTagInput.value = false
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
      reporter: reporterId.value,
      tags: selectedTags.value.map(tag => tag.id)
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
  
  // Fetch tags and other project data
  if (currentProject.value?.id) {
    console.log('Fetching project data for:', currentProject.value.id)
    const pid = currentProject.value.id
    
    await fetchTags()
    epics.value = (await axios.get(`/api/projects/${pid}/epics/`)).data
    sprints.value = (await axios.get(`/api/projects/${pid}/sprints/`)).data
    users.value = (await axios.get(`/api/projects/${currentProject.value.id}/users/`)).data
    console.log('Fetched project members:', users.value)
  }
})

watch(() => props.issue, (newIssue) => {
  if (props.mode === 'edit' && newIssue) {
    formData.value = {
      title: newIssue.title,
      description: newIssue.description,
      issue_type: newIssue.issue_type,
      epic: newIssue.epic,
      sprint: newIssue.sprint,
      assignee: newIssue.assignee,
      priority: newIssue.priority,
      story_points: newIssue.story_points,
      original_estimate: newIssue.original_estimate,
      remaining_estimate: newIssue.remaining_estimate
    }
    
    // Set selected tags for editing
    selectedTags.value = newIssue.tags || []
  }
})
</script>

<template>
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="issue-modal" @click.stop>
        <div class="modal-header">
          <div>
            <h2>{{ mode === 'edit' ? 'Edit Issue' : 'Create Issue' }}</h2>
            <p class="modal-subtitle">
              {{ mode === 'edit' 
                ? `Edit the issue in ${currentProject?.name || 'the project'}` 
                : `Add a new issue to ${currentProject?.name || 'the project'}` }}
            </p>
          </div>
          <button class="close-btn" @click="closeModal">×</button>
        </div>

      
      <div class="modal-body">
        <form @submit.prevent="saveIssue">
          
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

          
          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea
              v-model="formData.description"
              class="form-textarea"
              placeholder="Describe the issue in detail"
              rows="4"
            ></textarea>
          </div>

          
          <div class="form-group">
            <label class="form-label">Tags</label>
            
            
            <div v-if="selectedTags.length > 0" class="selected-tags">
              <div 
                v-for="tag in selectedTags" 
                :key="tag.id"
                class="tag-chip"
                :style="{ backgroundColor: tag.color }"
              >
                <span>{{ tag.name }}</span>
                <button 
                  type="button" 
                  class="tag-remove"
                  @click="removeTag(tag.id)"
                >
                  ×
                </button>
              </div>
            </div>

            
            <div class="tag-selector">
              <button
                type="button"
                class="add-tag-btn"
                @click="showTagDropdown = !showTagDropdown"
              >
                + Add Tag
              </button>

              
              <div v-if="showTagDropdown" class="tag-dropdown">
                
                <div v-if="filteredTags.length > 0" class="tag-section">
                  <div class="tag-section-title">Select existing tag</div>
                  <div class="tag-options">
                    <button
                      v-for="tag in filteredTags"
                      :key="tag.id"
                      type="button"
                      class="tag-option"
                      :style="{ borderColor: tag.color }"
                      @click="toggleTag(tag)"
                    >
                      <div class="tag-color" :style="{ backgroundColor: tag.color }"></div>
                      {{ tag.name }}
                    </button>
                  </div>
                </div>

                
                <div class="tag-section">
                  <div class="tag-section-title">Create new tag</div>
                  <div v-if="!showNewTagInput" class="create-tag-prompt">
                    <button
                      type="button"
                      class="create-tag-btn"
                      @click="showNewTagInput = true"
                    >
                      + Create new tag
                    </button>
                  </div>
                  <div v-else class="new-tag-input">
                    <input
                      v-model="newTagName"
                      type="text"
                      placeholder="Enter tag name"
                      class="tag-name-input"
                      @keyup.enter="createTag"
                      @keyup.escape="showNewTagInput = false; newTagName = ''"
                    />
                    <button
                      type="button"
                      class="create-tag-confirm"
                      @click="createTag"
                      :disabled="!newTagName.trim()"
                    >
                      Create
                    </button>
                    <button
                      type="button"
                      class="create-tag-cancel"
                      @click="showNewTagInput = false; newTagName = ''"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          
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

      
      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
        <button 
          type="button" 
          class="btn-primary" 
          @click="mode === 'edit' ? updateIssue() : saveIssue()"
          :disabled="isSubmitting"
        >
          <span v-if="isSubmitting">{{ mode === 'edit' ? 'Saving...' : 'Creating...' }}</span>
          <span v-else>{{ mode === 'edit' ? 'Save Changes' : 'Create Issue' }}</span>
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


.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  color: white;
  font-size: 0.8rem;
  font-weight: 500;
}

.tag-remove {
  background: none;
  border: none;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  padding: 0;
  margin-left: 0.25rem;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tag-remove:hover {
  background: rgba(255, 255, 255, 0.2);
}

.tag-selector {
  position: relative;
}

.add-tag-btn {
  background: #f8f9fa;
  border: 1px dashed #ddd;
  color: #666;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.add-tag-btn:hover {
  background: #e9ecef;
  border-color: #0066cc;
  color: #0066cc;
}

.tag-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-height: 300px;
  overflow-y: auto;
}

.tag-section {
  padding: 0.75rem;
}

.tag-section:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}

.tag-section-title {
  font-size: 0.8rem;
  font-weight: 500;
  color: #666;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tag-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.tag-option:hover {
  background: #f8f9fa;
}

.tag-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.create-tag-prompt {
  display: flex;
}

.create-tag-btn {
  background: #0066cc;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background-color 0.2s;
}

.create-tag-btn:hover {
  background: #0056b3;
}

.new-tag-input {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.tag-name-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
}

.create-tag-confirm,
.create-tag-cancel {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background-color 0.2s;
}

.create-tag-confirm {
  background: #28a745;
  color: white;
}

.create-tag-confirm:hover:not(:disabled) {
  background: #218838;
}

.create-tag-confirm:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.create-tag-cancel {
  background: #6c757d;
  color: white;
}

.create-tag-cancel:hover {
  background: #5a6268;
}


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
}


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
  .tag-dropdown {
      position: fixed;
      top: 50%;
      left: 1rem;
      right: 1rem;
      transform: translateY(-50%);
      max-height: 60vh;
      background: #232526 !important;
      border-color: #444 !important;
    }
}

@media (prefers-color-scheme: dark) {
  .modal-overlay {
    background: rgba(0, 0, 0, 0.8) !important;
  }

  .issue-modal,
  .modal-header,
  .modal-body,
  .modal-footer {
    background: #181a1b !important;
    color: #f3f3f3 !important;
    border-color: #333 !important;
  }

  .modal-header h2,
  .modal-subtitle,
  .form-label,
  .issue-type-name {
    color: #f3f3f3 !important;
  }

  .close-btn {
    color: #f3f3f3 !important;
  }

  .close-btn:hover {
    background: #333 !important;
  }

  .form-input,
  .form-select,
  .form-textarea {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .form-input:focus,
  .form-select:focus,
  .form-textarea:focus {
    border-color: #4ea1ff !important;
    box-shadow: 0 0 0 2px rgba(78, 161, 255, 0.1) !important;
  }

  .issue-type-option {
    background: #232526 !important;
    border-color: #444 !important;
    color: #f3f3f3 !important;
  }

  .issue-type-option:hover {
    border-color: #4ea1ff !important;
    background: #2a2d2e !important;
  }

  .issue-type-option.active {
    border-color: #4ea1ff !important;
    background: #1a2332 !important;
  }

  .assignee-preview {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }

  .assignee-avatar {
    background: #4ea1ff !important;
    color: #fff !important;
  }

  .btn-primary {
    background: #0056b3 !important;
    color: #fff !important;
  }

  .btn-primary:hover:not(:disabled) {
    background: #4ea1ff !important;
  }

  .btn-primary:disabled {
    background: #444 !important;
    color: #aaa !important;
  }

  .btn-secondary {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border: 1px solid #444 !important;
  }

  .btn-secondary:hover {
    background: #333 !important;
    border-color: #555 !important;
  }

   .add-tag-btn {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .add-tag-btn:hover {
    background: #2a2d2e !important;
    border-color: #4ea1ff !important;
    color: #4ea1ff !important;
  }

  .tag-dropdown {
    background: #232526 !important;
    border-color: #444 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  }

  .tag-section {
    border-bottom-color: #444 !important;
  }

  .tag-section-title {
    color: #aaa !important;
  }

  .tag-option {
    background: #181a1b !important;
    border-color: #444 !important;
    color: #f3f3f3 !important;
  }

  .tag-option:hover {
    background: #2a2d2e !important;
    border-color: #4ea1ff !important;
  }

  .create-tag-btn {
    background: #4ea1ff !important;
    color: #fff !important;
  }

  .create-tag-btn:hover {
    background: #0056b3 !important;
  }

  .tag-name-input {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .tag-name-input:focus {
    border-color: #4ea1ff !important;
    box-shadow: 0 0 0 2px rgba(78, 161, 255, 0.1) !important;
  }

  .create-tag-confirm {
    background: #28a745 !important;
  }

  .create-tag-confirm:hover:not(:disabled) {
    background: #218838 !important;
  }

  .create-tag-cancel {
    background: #444 !important;
    color: #f3f3f3 !important;
  }

  .create-tag-cancel:hover {
    background: #555 !important;
  }

}
</style>