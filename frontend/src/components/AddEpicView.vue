<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps({
  showModal: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'save'])

const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const users = ref([])

const formData = ref({
  title: '',
  description: '',
  assignee: null,
  status: 'to_do',
  priority: 'medium'
})

const priorities = [
  { value: 'lowest', label: 'Lowest' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'highest', label: 'Highest' }
]

const statuses = [
  { value: 'to_do', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' }
]

const errors = ref({})
const isSubmitting = ref(false)

const validateForm = () => {
  errors.value = {}
  if (!formData.value.title.trim()) errors.value.title = 'Title is required'
  return Object.keys(errors.value).length === 0
}

const resetForm = () => {
  formData.value = {
    title: '',
    description: '',
    assignee: null,
    status: 'to_do',
    priority: 'medium'
  }
  errors.value = {}
}

const closeModal = () => {
  resetForm()
  emit('close')
}

const saveEpic = async () => {
  if (!validateForm()) return
  isSubmitting.value = true
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    const epicData = {
      ...formData.value,
      project: currentProject.value?.id
    }
    await axios.post(`/api/projects/${currentProject.value.id}/epics/`, epicData)
    emit('save', epicData)
    closeModal()
  } catch (error) {
    console.error('Error saving epic:', error)
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  if (currentProject.value?.id) {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    users.value = (await axios.get(`/api/projects/${currentProject.value.id}/users/`)).data
  }
})
</script>

<template>
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="epic-modal" @click.stop>
      <div class="modal-header">
        <h2>Create Epic</h2>
        <button class="close-btn" @click="closeModal">×</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="saveEpic">
          <div class="form-group">
            <label class="form-label required">Title</label>
            <input
              v-model="formData.title"
              type="text"
              class="form-input"
              :class="{ error: errors.title }"
              placeholder="Epic title"
              maxlength="500"
            />
            <div v-if="errors.title" class="error-message">{{ errors.title }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea
              v-model="formData.description"
              class="form-textarea"
              placeholder="Describe the epic"
              rows="4"
            ></textarea>
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
            </div>
            <div class="form-group">
              <label class="form-label">Status</label>
              <select v-model="formData.status" class="form-select">
                <option v-for="status in statuses" :key="status.value" :value="status.value">
                  {{ status.label }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Priority</label>
              <select v-model="formData.priority" class="form-select">
                <option v-for="priority in priorities" :key="priority.value" :value="priority.value">
                  {{ priority.label }}
                </option>
              </select>
            </div>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
        <button
          type="button"
          class="btn-primary"
          @click="saveEpic"
          :disabled="isSubmitting"
        >
          <span v-if="isSubmitting">Creating...</span>
          <span v-else>Create Epic</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; overflow-y: auto; padding: 2rem;
}
.epic-modal {
  background: white; border-radius: 8px; max-width: 500px; width: 100%;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  overflow: hidden;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 2rem 2rem 1rem; border-bottom: 1px solid #e1e5e9;
}
.modal-header h2 { margin: 0; color: #333; font-size: 1.5rem; }
.close-btn {
  background: none; border: none; font-size: 1.5rem; color: #6c757d; cursor: pointer;
  padding: 0.25rem; border-radius: 4px; transition: background-color 0.2s;
}
.close-btn:hover { background: #f8f9fa; }
.modal-body { padding: 2rem; }
.modal-footer {
  display: flex; gap: 0.75rem; justify-content: flex-end;
  padding: 1rem 2rem 2rem; border-top: 1px solid #e1e5e9;
}
.form-group { margin-bottom: 1.5rem; }
.form-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.form-label { display: block; font-weight: 500; color: #333; margin-bottom: 0.5rem; font-size: 0.9rem; }
.form-label.required::after { content: ' *'; color: #dc3545; }
.form-input, .form-select, .form-textarea {
  width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 0.9rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none; border-color: #0066cc; box-shadow: 0 0 0 2px rgba(0,102,204,0.1);
}
.form-input.error { border-color: #dc3545; }
.form-textarea { resize: vertical; min-height: 100px; }
.error-message { color: #dc3545; font-size: 0.8rem; margin-top: 0.25rem; }
.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;
  transition: background-color 0.2s;
}
.btn-primary { background: #0066cc; color: white; }
.btn-primary:hover:not(:disabled) { background: #0056b3; }
.btn-primary:disabled { background: #6c757d; cursor: not-allowed; }
.btn-secondary { background: #6c757d; color: white; }
.btn-secondary:hover { background: #5a6268; }
@media (max-width: 768px) {
  .modal-overlay { padding: 1rem; }
  .form-row { grid-template-columns: 1fr; gap: 1rem; }
  .modal-header, .modal-body, .modal-footer { padding-left: 1.5rem; padding-right: 1.5rem; }
}
@media (prefers-color-scheme: dark) {
  .modal-overlay {
    background: rgba(0, 0, 0, 0.8) !important;
  }

  .epic-modal,
  .modal-header,
  .modal-body,
  .modal-footer {
    background: #181a1b !important;
    color: #f3f3f3 !important;
    border-color: #333 !important;
  }

  .modal-header h2,
  .form-label {
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

  .form-input.error {
    border-color: #dc3545 !important;
  }

  .error-message {
    color: #dc3545 !important;
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
}
</style>