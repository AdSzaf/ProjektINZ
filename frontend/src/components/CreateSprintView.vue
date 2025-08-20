<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

const props = defineProps({
  showModal: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'save'])

const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)

const formData = ref({
  name: '',
  goal: '',
  start_date: '',
  end_date: ''
})

const errors = ref({})
const isSubmitting = ref(false)

const validateForm = () => {
  errors.value = {}
  if (!formData.value.name.trim()) errors.value.name = 'Sprint name is required'
  if (!formData.value.start_date) errors.value.start_date = 'Start date is required'
  if (!formData.value.end_date) errors.value.end_date = 'End date is required'
  return Object.keys(errors.value).length === 0
}

const resetForm = () => {
  formData.value = {
    name: '',
    goal: '',
    start_date: '',
    end_date: ''
  }
  errors.value = {}
}

const closeModal = () => {
  resetForm()
  emit('close')
}

const saveSprint = async () => {
  if (!validateForm()) return
  isSubmitting.value = true
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    const sprintData = {
      ...formData.value,
      project: currentProject.value?.id
    }
    await axios.post(`/api/projects/${currentProject.value.id}/sprints/`, sprintData)
    emit('save', sprintData)
    closeModal()
  } catch (error) {
    console.error('Error saving sprint:', error)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Create Sprint</h2>
        <button class="close-btn" @click="closeModal">×</button>
      </div>
      <form @submit.prevent="saveSprint">
        <div class="form-group">
          <label class="form-label required">Sprint Name</label>
          <input
            v-model="formData.name"
            type="text"
            class="form-input"
            :class="{ error: errors.name }"
            placeholder="Sprint name"
            maxlength="100"
          />
          <div v-if="errors.name" class="error-message">{{ errors.name }}</div>
        </div>
        <div class="form-group">
          <label class="form-label">Goal</label>
          <textarea
            v-model="formData.goal"
            class="form-textarea"
            placeholder="Sprint goal"
            rows="2"
          ></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label required">Start Date</label>
            <input
              v-model="formData.start_date"
              type="date"
              class="form-input"
              :class="{ error: errors.start_date }"
            />
            <div v-if="errors.start_date" class="error-message">{{ errors.start_date }}</div>
          </div>
          <div class="form-group">
            <label class="form-label required">End Date</label>
            <input
              v-model="formData.end_date"
              type="date"
              class="form-input"
              :class="{ error: errors.end_date }"
            />
            <div v-if="errors.end_date" class="error-message">{{ errors.end_date }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            <span v-if="isSubmitting">Creating...</span>
            <span v-else>Create Sprint</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
  z-index: 1000; overflow-y: auto; padding: 2rem;
}
.modal-content {
  background: white; border-radius: 8px; max-width: 600px; width: 100%; /* <-- was 400px */
  box-shadow: 0 4px 20px rgba(0,0,0,0.15); overflow: hidden;
  padding: 2rem; /* Add more padding for better spacing */
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 0 1rem 0; border-bottom: 1px solid #e1e5e9;
}
.modal-header h2 { margin: 0; color: #333; font-size: 1.3rem; }
.close-btn {
  background: none; border: none; font-size: 1.5rem; color: #6c757d; cursor: pointer;
  padding: 0.25rem; border-radius: 4px; transition: background-color 0.2s;
}
.close-btn:hover { background: #f8f9fa; }
.form-group { margin-bottom: 1.2rem; }
.form-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
.form-label { display: block; font-weight: 500; color: #333; margin-bottom: 0.5rem; font-size: 0.9rem; }
.form-label.required::after { content: ' *'; color: #dc3545; }
.form-input, .form-textarea {
  width: 100%; padding: 0.7rem; border: 1px solid #ddd; border-radius: 4px; font-size: 0.9rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:focus, .form-textarea:focus {
  outline: none; border-color: #0066cc; box-shadow: 0 0 0 2px rgba(0,102,204,0.1);
}
.form-input.error { border-color: #dc3545; }
.form-textarea { resize: vertical; min-height: 60px; }
.error-message { color: #dc3545; font-size: 0.8rem; margin-top: 0.25rem; }
.btn-primary, .btn-secondary {
  padding: 0.7rem 1.3rem; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;
  transition: background-color 0.2s;
}
.btn-primary { background: #0066cc; color: white; }
.btn-primary:hover:not(:disabled) { background: #0056b3; }
.btn-primary:disabled { background: #6c757d; cursor: not-allowed; }
.btn-secondary { background: #6c757d; color: white; }
.btn-secondary:hover { background: #5a6268; }
@media (max-width: 600px) {
  .modal-overlay { padding: 1rem; }
  .modal-content { max-width: 98vw; padding: 1rem; }
  .form-row { grid-template-columns: 1fr; gap: 1rem; }
  .modal-header, .modal-footer { padding-left: 0; padding-right: 0; }
}
</style>