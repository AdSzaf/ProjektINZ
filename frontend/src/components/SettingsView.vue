<script setup>
import { ref, reactive } from 'vue'
import { onMounted } from 'vue'
import axios from 'axios'
import { useProjectStore } from '../stores/projectStore'

// Form data
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)

const profile = reactive({
  name: '',
  email: '',
  role: '',
  department: ''
})

const notifications = reactive({
  email: true,
  push: true,
  weeklyDigest: false
})

const preferences = reactive({
  theme: 'light',
  language: 'en',
  timezone: 'UTC',
  dateFormat: 'MM/DD/YYYY'
})

const security = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  twoFactorEnabled: false
})

// UI state
const showDeleteConfirm = ref(false)
const showSuccessToast = ref(false)
const successMessage = ref('')

// Methods
const showToast = (message) => {
  successMessage.value = message
  showSuccessToast.value = true
  setTimeout(() => {
    showSuccessToast.value = false
  }, 3000)
}

const fetchProfile = async () => {
  const token = localStorage.getItem('token')
  if (!token) return
  if (token) {
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
    }
  const res = await axios.get('/api/me/')
  profile.name = `${res.data.first_name} ${res.data.last_name}`
  profile.email = res.data.email
  profile.role = res.data.role
  // Add department if you have it
}

const saveProfile = () => {
  // Save profile logic here
  console.log('Saving profile:', profile)
  showToast('Profile updated successfully!')
}

const resetProfile = () => {
  profile.name = 'John Doe'
  profile.email = 'john.doe@company.com'
  profile.role = 'Developer'
  profile.department = 'Engineering'
  showToast('Profile reset to defaults')
}

const saveNotifications = () => {
  console.log('Saving notifications:', notifications)
  showToast('Notification settings saved!')
}

const savePreferences = () => {
  console.log('Saving preferences:', preferences)
  showToast('Display preferences updated!')
}

const updatePassword = () => {
  if (security.newPassword !== security.confirmPassword) {
    alert('New passwords do not match!')
    return
  }
  if (security.newPassword.length < 8) {
    alert('Password must be at least 8 characters long!')
    return
  }
  
  console.log('Updating password')
  security.currentPassword = ''
  security.newPassword = ''
  security.confirmPassword = ''
  showToast('Password updated successfully!')
}

const exportData = () => {
  console.log('Exporting account data')
  showToast('Account data export started!')
}

const deleteAccount = () => {
  console.log('Deleting account')
  showDeleteConfirm.value = false
  // Handle account deletion
  alert('Account deletion would be processed here')
}

onMounted(fetchProfile)
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <h1>Settings</h1>
      <p class="settings-description">Manage your account preferences and application settings</p>
    </div>

    <div class="settings-container">
      <!-- Profile Settings -->
      <div class="settings-section">
        <h2>Profile Information</h2>
        <div class="settings-card">
          <div class="form-group">
            <label for="fullName">Full Name</label>
            <input 
              id="fullName"
              type="text" 
              v-model="profile.name"
              placeholder="Enter your full name"
            />
          </div>
          
          <div class="form-group">
            <label for="email">Email Address</label>
            <input 
              id="email"
              type="email" 
              v-model="profile.email"
              placeholder="Enter your email"
            />
          </div>
          
          <div class="form-group">
            <label for="role">Role</label>
            <select id="role" v-model="profile.role">
              <option value="Developer">Developer</option>
              <option value="Product Manager">Product Manager</option>
              <option value="Designer">Designer</option>
              <option value="QA Engineer">QA Engineer</option>
              <option value="Team Lead">Team Lead</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="department">Department</label>
            <input 
              id="department"
              type="text" 
              v-model="profile.department"
              placeholder="Enter your department"
            />
          </div>
          
          <div class="form-actions">
            <button class="btn-primary" @click="saveProfile">Save Profile</button>
            <button class="btn-secondary" @click="resetProfile">Reset</button>
          </div>
        </div>
      </div>

      <!-- Notification Settings -->
      <div class="settings-section">
        <h2>Notifications</h2>
        <div class="settings-card">
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                type="checkbox" 
                id="emailNotifications" 
                v-model="notifications.email"
              />
              <label for="emailNotifications">Email Notifications</label>
            </div>
            <p class="help-text">Receive email updates for assigned issues and mentions</p>
          </div>
          
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                type="checkbox" 
                id="pushNotifications" 
                v-model="notifications.push"
              />
              <label for="pushNotifications">Push Notifications</label>
            </div>
            <p class="help-text">Get browser notifications for real-time updates</p>
          </div>
          
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                type="checkbox" 
                id="weeklyDigest" 
                v-model="notifications.weeklyDigest"
              />
              <label for="weeklyDigest">Weekly Digest</label>
            </div>
            <p class="help-text">Receive a weekly summary of your project activities</p>
          </div>
          
          <div class="form-actions">
            <button class="btn-primary" @click="saveNotifications">Save Notifications</button>
          </div>
        </div>
      </div>

      <!-- Display Preferences -->
      <div class="settings-section">
        <h2>Display Preferences</h2>
        <div class="settings-card">
          <div class="form-group">
            <label for="theme">Theme</label>
            <select id="theme" v-model="preferences.theme">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="language">Language</label>
            <select id="language" v-model="preferences.language">
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="timezone">Timezone</label>
            <select id="timezone" v-model="preferences.timezone">
              <option value="UTC">UTC (Coordinated Universal Time)</option>
              <option value="EST">EST (Eastern Standard Time)</option>
              <option value="PST">PST (Pacific Standard Time)</option>
              <option value="GMT">GMT (Greenwich Mean Time)</option>
              <option value="CET">CET (Central European Time)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="dateFormat">Date Format</label>
            <select id="dateFormat" v-model="preferences.dateFormat">
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button class="btn-primary" @click="savePreferences">Save Preferences</button>
          </div>
        </div>
      </div>

      <!-- Security Settings -->
      <div class="settings-section">
        <h2>Security</h2>
        <div class="settings-card">
          <div class="form-group">
            <label for="currentPassword">Current Password</label>
            <input 
              id="currentPassword"
              type="password" 
              v-model="security.currentPassword"
              placeholder="Enter current password"
            />
          </div>
          
          <div class="form-group">
            <label for="newPassword">New Password</label>
            <input 
              id="newPassword"
              type="password" 
              v-model="security.newPassword"
              placeholder="Enter new password"
            />
          </div>
          
          <div class="form-group">
            <label for="confirmPassword">Confirm New Password</label>
            <input 
              id="confirmPassword"
              type="password" 
              v-model="security.confirmPassword"
              placeholder="Confirm new password"
            />
          </div>
          
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                type="checkbox" 
                id="twoFactor" 
                v-model="security.twoFactorEnabled"
              />
              <label for="twoFactor">Enable Two-Factor Authentication</label>
            </div>
            <p class="help-text">Add an extra layer of security to your account</p>
          </div>
          
          <div class="form-actions">
            <button class="btn-primary" @click="updatePassword">Update Password</button>
          </div>
        </div>
      </div>

      <!-- Account Actions -->
      <div class="settings-section">
        <h2>Account Actions</h2>
        <div class="settings-card">
          <div class="form-group">
            <button class="btn-secondary" @click="exportData">
              📊 Export Account Data
            </button>
            <p class="help-text">Download a copy of your account data and activity</p>
          </div>
          
          <div class="form-group danger-zone">
            <h3>Danger Zone</h3>
            <button class="btn-danger" @click="showDeleteConfirm = true">
              🗑️ Delete Account
            </button>
            <p class="help-text">Permanently delete your account and all associated data</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="showDeleteConfirm = false">
      <div class="modal" @click.stop>
        <h3>Delete Account</h3>
        <p>Are you sure you want to delete your account? This action cannot be undone.</p>
        <div class="modal-actions">
          <button class="btn-danger" @click="deleteAccount">Yes, Delete Account</button>
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Success Toast -->
    <div v-if="showSuccessToast" class="toast success-toast">
      ✅ {{ successMessage }}
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2rem;
}

.settings-description {
  color: #666;
  margin: 0;
  font-size: 1.1rem;
}

.settings-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-section h2 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.5rem;
}

.settings-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.checkbox-group label {
  margin: 0;
  font-weight: 500;
  cursor: pointer;
}

.help-text {
  font-size: 0.9rem;
  color: #666;
  margin: 0.5rem 0 0 0;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e1e5e9;
}

.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
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

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-danger:hover {
  background: #c0392b;
}

.danger-zone {
  border: 1px solid #e74c3c;
  border-radius: 4px;
  padding: 1rem;
  background: #fef5f5;
}

.danger-zone h3 {
  margin: 0 0 0.5rem 0;
  color: #e74c3c;
  font-size: 1.1rem;
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

.modal {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.modal p {
  margin: 0 0 1.5rem 0;
  color: #666;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

/* Toast */
.toast {
  position: fixed;
  top: 80px;
  right: 1rem;
  background: #28a745;
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .settings-page {
    margin: 0;
    padding: 0 1rem;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .modal-actions {
    flex-direction: column;
  }
}
</style>