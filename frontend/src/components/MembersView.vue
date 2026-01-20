<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

// UI State
const viewMode = ref('grid') // 'grid' or 'list'
const searchQuery = ref('')
const selectedRole = ref('all')
const selectedStatus = ref('all')
const showInviteModal = ref(false)
const showMemberDetails = ref(false)
const selectedMember = ref(null)
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)
const currentUserId = ref('')
const currentUserEmail = ref('')

// Invite request state
const isInviting = ref(false)
const inviteError = ref('')
const inviteSuccess = ref('')

// Member status update state
const tempStatus = ref('active')
const isUpdatingStatus = ref(false)
const statusError = ref('')
const statusSuccess = ref('')
const showStatusModal = ref(false)

// Filter options
const roleOptions = [
  { value: 'all', label: 'All Roles' },
  { value: 'admin', label: 'Admin' },
  { value: 'product-manager', label: 'Product Manager' },
  { value: 'developer', label: 'Developer' },
  { value: 'designer', label: 'Designer' },
  { value: 'qa', label: 'QA Engineer' },
  { value: 'devops', label: 'DevOps' }
]

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'active', label: 'Active' },
  { value: 'busy', label: 'Busy' },
  { value: 'away', label: 'Away' },
  { value: 'offline', label: 'Offline' }
]

const teamMembers = ref([])

// Invite form data
const inviteForm = ref({
  email: '',
  role: 'developer',
  message: ''
})

// Computed properties
const filteredMembers = computed(() => {
  return teamMembers.value.filter(member => {
    const matchesSearch = member.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         member.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         member.roleDisplay.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesRole = selectedRole.value === 'all' || member.role === selectedRole.value
    const matchesStatus = selectedStatus.value === 'all' || member.status === selectedStatus.value
    
    return matchesSearch && matchesRole && matchesStatus
  })
})

const teamStats = computed(() => {
  const totalMembers = teamMembers.value.length
  const activeMembers = teamMembers.value.filter(m => m.status === 'active').length
  const totalIssues = teamMembers.value.reduce((sum, m) => sum + m.assignedIssues, 0)
  const avgWorkload = Math.round(teamMembers.value.reduce((sum, m) => sum + m.workload, 0) / totalMembers)
  
  return { totalMembers, activeMembers, totalIssues, avgWorkload }
})

// Methods
const getStatusColor = (status) => {
  const colors = {
    active: '#28a745',
    busy: '#dc3545',
    away:  '#ffc107',
    offline: '#6c757d'
  }
  return colors[status] || '#6c757d'
}

const getWorkloadColor = (workload) => {
  if (workload >= 90) return '#dc3545'
  if (workload >= 80) return '#ffc107'
  if (workload >= 70) return '#007bff'
  return '#28a745'
}

const openMemberDetails = (member) => {
  selectedMember.value = member
  showMemberDetails.value = true
  tempStatus.value = member.status || 'active'
  statusError.value = ''
  statusSuccess.value = ''
}

const closeMemberDetails = () => {
  showMemberDetails.value = false
  selectedMember.value = null
}

const openStatusModal = (member) => {
  // Only allow opening for your own card (match by id or email)
  const isSelf = (currentUserId.value && member.id === currentUserId.value) ||
                 (currentUserEmail.value && member.email === currentUserEmail.value)
  if (!isSelf) return
  tempStatus.value = member.status || 'active'
  selectedMember.value = member
  statusError.value = ''
  statusSuccess.value = ''
  showStatusModal.value = true
}

const closeStatusModal = () => {
  showStatusModal.value = false
}

const openInviteModal = () => {
  showInviteModal.value = true
  inviteError.value = ''
  inviteSuccess.value = ''
}

const closeInviteModal = () => {
  showInviteModal.value = false
  inviteForm.value = { email: '', role: 'developer', message: '' }
  isInviting.value = false
  inviteError.value = ''
  inviteSuccess.value = ''
}

const sendInvite = async () => {
  inviteError.value = ''
  inviteSuccess.value = ''
  // basic email validation
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailPattern.test(inviteForm.value.email)) {
    inviteError.value = 'Please enter a valid email address.'
    return
  }
  if (!currentProject.value?.id) {
    inviteError.value = 'No project selected.'
    return
  }
  try {
    isInviting.value = true
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    // Backend to be implemented: accept { email, role, message }
    await axios.post(`/api/projects/${currentProject.value.id}/invite/`, {
      email: inviteForm.value.email,
      role: inviteForm.value.role,
      message: inviteForm.value.message,
    })
    inviteSuccess.value = 'Invitation sent successfully.'
    // Refresh members in case backend adds immediately when existing user
    await fetchTeamMembers()
    // Optionally close after a short delay
    setTimeout(() => {
      closeInviteModal()
    }, 800)
  } catch (err) {
    const msg = err?.response?.data?.detail || 'Failed to send invitation.'
    inviteError.value = msg
  } finally {
    isInviting.value = false
  }
}

const updateMemberStatus = async () => {
  statusError.value = ''
  statusSuccess.value = ''
  if (!selectedMember.value || !currentProject.value?.id) return
  const desired = tempStatus.value
  if (!['active','busy','away','offline'].includes(desired)) {
    statusError.value = 'Invalid status.'
    return
  }
  try {
    isUpdatingStatus.value = true
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    await axios.post(`/api/projects/${currentProject.value.id}/member-statuses/${selectedMember.value.id}/`, {
      status: desired,
    })
    // Update local state
    const idx = teamMembers.value.findIndex(m => m.id === selectedMember.value.id)
    if (idx !== -1) {
      teamMembers.value[idx] = { ...teamMembers.value[idx], status: desired }
    }
    selectedMember.value = { ...selectedMember.value, status: desired }
    statusSuccess.value = 'Status updated.'
  } catch (err) {
    statusError.value = err?.response?.data?.detail || 'Failed to update status.'
  } finally {
    isUpdatingStatus.value = false
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// Close modals when clicking outside
const closeModals = (event) => {
  if (event.target.classList.contains('modal-overlay')) {
    showMemberDetails.value = false
    showInviteModal.value = false
    showStatusModal.value = false
  }
}


const fetchTeamMembers = async () => {
  if (!currentProject.value?.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/users/`)
  // Map backend data to frontend format if needed
  teamMembers.value = res.data.map(u => ({
    id: u.id,
    name: u.name || `${u.first_name} ${u.last_name}`,
    email: u.email,
    avatar: (u.first_name?.[0] || '') + (u.last_name?.[0] || ''),
    role: u.role || 'developer',
    roleDisplay: u.role ? u.role.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Developer',
    status: u.status || 'active',
    location: u.location || '',
    timezone: u.timezone || '',
    joinDate: u.joined_at || '',
    assignedIssues: u.assigned_issues || 0,
    completedIssues: u.completed_issues || 0,
    currentSprint: u.current_sprint || '',
    workload: u.workload || 0,
    skills: u.skills || [],
    bio: u.bio || '',
    recentActivity: u.recent_activity || [],
    socialLinks: u.social_links || {}
  }))
  console.log('Fetched team members:', teamMembers.value)
  // If we have the current user's email but not their id, match and set it
  if (currentUserEmail.value && !currentUserId.value) {
    const me = teamMembers.value.find(m => m.email === currentUserEmail.value)
    if (me) currentUserId.value = me.id
  }
}

onMounted(() => {
  fetchTeamMembers()
  // Load current user id
  const token = localStorage.getItem('token')
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    axios.get('/api/me/').then(r => {
      currentUserId.value = r.data.id || ''
      currentUserEmail.value = r.data.email || ''
    }).catch(() => {})
  }
})

watch(currentProject, (newVal) => {
  if (newVal?.id) fetchTeamMembers()
})
</script>

<template>
  <div v-if="!currentProject" class="no-projects-message">
    <h2>No projects found</h2>
    <p>Create your first project to get started!</p>
    <button class="btn btn-primary" @click="$router.push('/create-project')">+ Create Project</button>
  </div>
  <div v-else class="team-members-container">
    
    <div class="team-header">
      <div class="header-content">
        <h1>Team Members</h1>
        <p class="team-description">Manage your team, track workload, and collaborate effectively</p>
      </div>
      
      <button class="invite-btn" @click="openInviteModal">
        + Invite Member
      </button>
    </div>

    
    <div class="team-stats">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <div class="stat-number">{{ teamStats.totalMembers }}</div>
          <div class="stat-label">Total Members</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🟢</div>
        <div class="stat-info">
          <div class="stat-number">{{ teamStats.activeMembers }}</div>
          <div class="stat-label">Active Now</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-number">{{ teamStats.totalIssues }}</div>
          <div class="stat-label">Assigned Issues</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-info">
          <div class="stat-number">{{ teamStats.avgWorkload }}%</div>
          <div class="stat-label">Avg Workload</div>
        </div>
      </div>
    </div>

    
    <div class="team-controls">
      <div class="search-filters">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Search members..."
            class="search-input"
          />
          <span class="search-icon">🔍</span>
        </div>
        
        <select v-model="selectedRole" class="filter-select">
          <option v-for="role in roleOptions" :key="role.value" :value="role.value">
            {{ role.label }}
          </option>
        </select>
        
        <select v-model="selectedStatus" class="filter-select">
          <option v-for="status in statusOptions" :key="status.value" :value="status.value">
            {{ status.label }}
          </option>
        </select>
      </div>
      
      <div class="view-controls">
        <button 
          class="view-btn" 
          :class="{ active: viewMode === 'grid' }"
          @click="viewMode = 'grid'"
        >
          📱 Grid
        </button>
        <button 
          class="view-btn" 
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          📄 List
        </button>
      </div>
    </div>

    
    <div class="members-container" :class="{ 'list-view': viewMode === 'list' }">
      <div 
        v-for="member in filteredMembers" 
        :key="member.id"
        class="member-card"
        @click="openMemberDetails(member)"
      >
        <div class="member-header">
          <div class="member-avatar-container" @click.stop="openStatusModal(member)" :title="member.id === currentUserId ? 'Click to change your status' : ''">
            <div class="member-avatar">{{ member.avatar }}</div>
            <div 
              class="status-indicator" 
              :style="{ backgroundColor: getStatusColor(member.status) }"
            ></div>
          </div>
          
          <div class="member-info">
            <h3 class="member-name">{{ member.name }}</h3>
            <p class="member-role">{{ member.roleDisplay }}</p>
            <p class="member-location">📍 {{ member.location }}</p>
          </div>
          
          <div class="member-stats" v-if="viewMode === 'grid'">
            <div class="stat-item">
              <span class="stat-number">{{ member.assignedIssues }}</span>
              <span class="stat-label">Issues</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ member.currentSprint }}</span>
              <span class="stat-label">Sprint</span>
            </div>
          </div>
        </div>
        
        <div class="member-details">
          <div class="workload-section">
            <div class="workload-header">
              <span class="workload-label">Workload</span>
              <span class="workload-percentage" :style="{ color: getWorkloadColor(member.workload) }">
                {{ member.workload }}%
              </span>
            </div>
            <div class="workload-bar">
              <div 
                class="workload-fill" 
                :style="{ 
                  width: member.workload + '%', 
                  backgroundColor: getWorkloadColor(member.workload) 
                }"
              ></div>
            </div>
          </div>
          
          <div class="skills-section" v-if="viewMode === 'grid'">
            <div class="skills-list">
              <span 
                v-for="skill in member.skills.slice(0, 3)" 
                :key="skill"
                class="skill-tag"
              >
                {{ skill }}
              </span>
              <span v-if="member.skills.length > 3" class="skill-tag more">
                +{{ member.skills.length - 3 }}
              </span>
            </div>
          </div>
        </div>
        
        
        <div v-if="viewMode === 'list'" class="member-list-details">
          <div class="list-stats">
            <span class="list-stat">{{ member.assignedIssues }} Issues</span>
            <span class="list-stat">{{ member.completedIssues }} Completed</span>
            <span class="list-stat">Sprint {{ member.currentSprint }}</span>
          </div>
          <div class="list-contact">
            <span class="contact-email">{{ member.email }}</span>
            <span class="contact-timezone">{{ member.timezone }}</span>
          </div>
        </div>
      </div>
    </div>

    
    <div v-if="showMemberDetails" class="modal-overlay" @click="closeModals">
      <div class="modal-content member-modal">
        <div class="modal-header">
          <h2>Team Member Details</h2>
          <div class="header-actions">
            <button 
              v-if="selectedMember && selectedMember.id === currentUserId"
              class="send-btn edit-status-btn" 
              @click.stop="openStatusModal(selectedMember)"
            >
              Edit Status
            </button>
            <button class="close-btn" @click="closeMemberDetails">×</button>
          </div>
        </div>
        
        <div v-if="selectedMember" class="member-details-content">
          <div class="member-profile">
            <div class="profile-left">
              <div class="large-avatar-container">
                <div class="large-avatar">{{ selectedMember.avatar }}</div>
                <div 
                  class="large-status-indicator" 
                  :style="{ backgroundColor: getStatusColor(selectedMember.status) }"
                ></div>
              </div>
            </div>
            
            <div class="profile-right">
              <h3>{{ selectedMember.name }}</h3>
              <p class="profile-role">{{ selectedMember.roleDisplay }}</p>
              <p class="profile-bio">{{ selectedMember.bio }}</p>
              
              <div class="profile-details">
                <div class="detail-item">
                  <strong>Email:</strong> {{ selectedMember.email }}
                </div>
                <div class="detail-item">
                  <strong>Location:</strong> {{ selectedMember.location }}
                </div>
                <div class="detail-item">
                  <strong>Timezone:</strong> {{ selectedMember.timezone }}
                </div>
                <div class="detail-item">
                  <strong>Joined:</strong> {{ formatDate(selectedMember.joinDate) }}
                </div>
              </div>
              
              <div class="social-links" v-if="selectedMember.socialLinks">
                <a v-if="selectedMember.socialLinks.linkedin" :href="selectedMember.socialLinks.linkedin" target="_blank" class="social-link">
                  💼 LinkedIn
                </a>
                <a v-if="selectedMember.socialLinks.github" :href="selectedMember.socialLinks.github" target="_blank" class="social-link">
                  🐙 GitHub
                </a>
                <a v-if="selectedMember.socialLinks.twitter" :href="selectedMember.socialLinks.twitter" target="_blank" class="social-link">
                  🐦 Twitter
                </a>
              </div>
            </div>
          </div>
          
          <div class="member-stats-grid">
            <div class="stats-card">
              <h4>Work Statistics</h4>
              <div class="stats-list">
                <div class="stat-row">
                  <span>Assigned Issues:</span>
                  <span class="stat-value">{{ selectedMember.assignedIssues }}</span>
                </div>
                <div class="stat-row">
                  <span>Completed Issues:</span>
                  <span class="stat-value">{{ selectedMember.completedIssues }}</span>
                </div>
                <div class="stat-row">
                  <span>Current Sprint Issues:</span>
                  <span class="stat-value">{{ selectedMember.currentSprint }}</span>
                </div>
                <div class="stat-row">
                  <span>Workload:</span>
                  <span class="stat-value" :style="{ color: getWorkloadColor(selectedMember.workload) }">
                    {{ selectedMember.workload }}%
                  </span>
                </div>
              </div>
            </div>
            
            <div class="skills-card">
              <h4>Skills & Expertise</h4>
              <div class="skills-grid">
                <span 
                  v-for="skill in selectedMember.skills" 
                  :key="skill"
                  class="skill-badge"
                >
                  {{ skill }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="recent-activity-card">
            <h4>Recent Activity</h4>
            <div class="activity-list">
              <div 
                v-for="activity in selectedMember.recentActivity" 
                :key="activity.item"
                class="activity-item"
              >
                <div class="activity-content">
                  <span class="activity-action">{{ activity.action }}</span>
                  <span class="activity-item-name">{{ activity.item }}</span>
                </div>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    
    <div v-if="showInviteModal" class="modal-overlay" @click="closeModals">
      <div class="modal-content invite-modal">
        <div class="modal-header">
          <h2>Invite Team Member</h2>
          <button class="close-btn" @click="closeInviteModal">×</button>
        </div>
        
        <div class="invite-form">
          <div v-if="inviteError" class="alert error">{{ inviteError }}</div>
          <div v-if="inviteSuccess" class="alert success">{{ inviteSuccess }}</div>
          <div class="form-group">
            <label for="invite-email">Email Address</label>
            <input 
              id="invite-email"
              type="email" 
              v-model="inviteForm.email"
              placeholder="colleague@company.com"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="invite-role">Role</label>
            <select id="invite-role" v-model="inviteForm.role" class="form-select">
              <option value="developer">Developer</option>
              <option value="designer">Designer</option>
              <option value="qa">QA Engineer</option>
              <option value="product-manager">Product Manager</option>
              <option value="devops">DevOps</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="invite-message">Personal Message (Optional)</label>
            <textarea 
              id="invite-message"
              v-model="inviteForm.message"
              placeholder="Welcome to our team! Looking forward to working with you."
              class="form-textarea"
            ></textarea>
          </div>
          
          <div class="form-actions">
            <button class="cancel-btn" @click="closeInviteModal">Cancel</button>
            <button class="send-btn" @click="sendInvite" :disabled="isInviting || !inviteForm.email">
              {{ isInviting ? 'Sending…' : 'Send Invitation' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  
  <div v-if="showStatusModal" class="modal-overlay" @click="closeModals">
    <div class="modal-content invite-modal" @click.stop>
      <div class="modal-header">
        <h2>Update Status</h2>
        <button class="close-btn" @click="closeStatusModal">×</button>
      </div>
      <div class="invite-form">
        <div v-if="statusError" class="alert error">{{ statusError }}</div>
        <div v-if="statusSuccess" class="alert success">{{ statusSuccess }}</div>
        <div class="form-group">
          <label for="status-select">Your status</label>
          <select id="status-select" v-model="tempStatus" class="form-select">
            <option value="active">Active</option>
            <option value="busy">Busy</option>
            <option value="away">Away</option>
            <option value="offline">Offline</option>
          </select>
        </div>
        <div class="form-actions">
          <button class="cancel-btn" @click="closeStatusModal">Cancel</button>
          <button class="send-btn" @click="updateMemberStatus" :disabled="isUpdatingStatus">
            {{ isUpdatingStatus ? 'Updating…' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.team-members-container {
  max-width: 1400px;
  margin: 0 auto;
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-content h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2rem;
}

.team-description {
  color: #666;
  margin: 0;
  font-size: 1.1rem;
}

.invite-btn {
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.75rem 1.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.invite-btn:hover {
  background: #0056b3;
}

.team-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #0066cc;
  margin: 0;
  display: block;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin: 0;
}

.team-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
}

.search-filters {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-box {
  position: relative;
}

.search-input {
  padding: 0.5rem 2.5rem 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  min-width: 250px;
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: #0066cc;
}

.search-icon {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
}

.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 0.9rem;
  min-width: 150px;
  color: #222;
}

.filter-select:focus {
  outline: none;
  border-color: #0066cc;
  color: #222;
}

.view-controls {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  color: #222;
}

.view-btn:hover {
  background: #f8f9fa;
}

.view-btn.active {
  background: #0066cc;
  color: white;
  border-color: #0066cc;
}

.members-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.members-container.list-view {
  grid-template-columns: 1fr;
}

.member-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.member-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.member-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.member-avatar-container {
  position: relative;
  flex-shrink: 0;
}

.member-avatar {
  width: 60px;
  height: 60px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}

.status-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid white;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 1.1rem;
}

.member-role {
  margin: 0 0 0.25rem 0;
  color: #0066cc;
  font-weight: 500;
  font-size: 0.9rem;
}

.member-location {
  margin: 0;
  color: #666;
  font-size: 0.8rem;
}

.member-stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-item .stat-number {
  font-size: 1.2rem;
  font-weight: bold;
  color: #0066cc;
  margin: 0;
}

.stat-item .stat-label {
  font-size: 0.7rem;
  color: #666;
  margin: 0;
}

.member-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.workload-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.workload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.workload-label {
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
}

.workload-percentage {
  font-size: 0.9rem;
  font-weight: bold;
}

.workload-bar {
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.workload-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 3px;
}

.skills-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.skill-tag {
  background: #f8f9fa;
  color: #333;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  border: 1px solid #e9ecef;
}

.skill-tag.more {
  background: #0066cc;
  color: white;
  border-color: #0066cc;
}

.member-list-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
  margin-top: 1rem;
}

.list-stats {
  display: flex;
  gap: 1rem;
}

.list-stat {
  font-size: 0.9rem;
  color: #666;
}

.list-contact {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.contact-email {
  font-size: 0.9rem;
  color: #0066cc;
}

.contact-timezone {
  font-size: 0.8rem;
  color: #666;
}


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
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.member-modal {
  max-width: 800px;
}

.invite-modal {
  max-width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h2 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #f8f9fa;
}

.member-details-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.member-profile {
  display: flex;
  gap: 2rem;
}

.profile-left {
  flex-shrink: 0;
}

.large-avatar-container {
  position: relative;
}

.large-avatar {
  width: 120px;
  height: 120px;
  background: #0066cc;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 2rem;
}

.large-status-indicator {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 4px solid white;
}

.profile-right {
  flex: 1;
}

.profile-right h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.profile-role {
  margin: 0 0 1rem 0;
  color: #0066cc;
  font-weight: 500;
  font-size: 1.1rem;
}

.profile-bio {
  margin: 0 0 1.5rem 0;
  color: #666;
  line-height: 1.5;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.detail-item {
  font-size: 0.9rem;
  color: #333;
}

.detail-item strong {
  color: #333;
  min-width: 80px;
  display: inline-block;
}

.social-links {
  display: flex;
  gap: 1rem;
}

.social-link {
  color: #0066cc;
  text-decoration: none;
  font-size: 0.9rem;
  padding: 0.5rem 1rem;
  border: 1px solid #0066cc;
  border-radius: 4px;
  transition: all 0.2s;
}

.social-link:hover {
  background: #0066cc;
  color: white;
}

.member-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.stats-card, .skills-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 1.5rem;
}

.stats-card h4, .skills-card h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.stat-value {
  font-weight: bold;
  color: #0066cc;
}

.skills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.skill-badge {
  background: white;
  color: #333;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  border: 1px solid #e9ecef;
  font-weight: 500;
}

.recent-activity-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 1.5rem;
}

.recent-activity-card h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.edit-status-btn {
  padding: 0.5rem 0.9rem;
}

.status-controls {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.activity-content {
  flex: 1;
}

.activity-action {
  color: #666;
  margin-right: 0.5rem;
}

.activity-item-name {
  font-weight: 500;
  color: #333;
}

.activity-time {
  font-size: 0.8rem;
  color: #999;
  white-space: nowrap;
}


.invite-form {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.form-input, .form-select, .form-textarea {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #0066cc;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.cancel-btn, .send-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: white;
  border: 1px solid #ddd;
  color: #333;
}

.cancel-btn:hover {
  background: #f8f9fa;
}

.send-btn {
  background: #0066cc;
  border: 1px solid #0066cc;
  color: white;
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
}

.send-btn:disabled {
  background: #6c757d;
  border-color: #6c757d;
  cursor: not-allowed;
}


.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
}

.alert.error {
  background: #ffe3e3;
  border: 1px solid #ffc9c9;
  color: #c92a2a;
}

.alert.success {
  background: #e6fcf5;
  border: 1px solid #c3fae8;
  color: #087f5b;
}


@media (max-width: 1024px) {
  .member-stats-grid {
    grid-template-columns: 1fr;
  }
  
  .member-profile {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .team-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .team-controls {
    flex-direction: column;
    gap: 1rem;
  }
  
  .search-filters {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .search-input {
    min-width: 100%;
  }
  
  .members-container {
    grid-template-columns: 1fr;
  }
  
  .member-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .member-stats {
    flex-direction: row;
    justify-content: space-around;
  }
  
  .modal-content {
    margin: 0.5rem;
    max-height: 95vh;
  }
  
  .member-details-content {
    padding: 1rem;
  }
  
  .invite-form {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .team-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stat-card {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 1.5rem;
  }
  
  .view-controls {
    width: 100%;
    justify-content: center;
  }
  
  .form-actions {
    flex-direction: column;
  }
}

@media (prefers-color-scheme: dark) {
  
  .team-members-container,
  .team-header,
  .team-stats,
  .team-controls,
  .members-container,
  .stat-card,
  .member-card,
  .search-filters,
  .modal-overlay,
  .modal-content,
  .member-modal,
  .invite-modal,
  .member-details-content,
  .stats-card,
  .skills-card,
  .recent-activity-card,
  .invite-form,
  .activity-item,
  .member-profile,
  .profile-left,
  .profile-right {
    background: #181a1b !important;
    color: #f3f3f3 !important;
    border-color: #333 !important;
  }

  
  .header-content h1,
  .team-description,
  .stat-number,
  .stat-label,
  .member-name,
  .member-role,
  .member-location,
  .workload-label,
  .workload-percentage,
  .contact-email,
  .contact-timezone,
  .list-stat,
  .modal-header h2,
  .profile-role,
  .profile-bio,
  .detail-item,
  .detail-item strong,
  .stats-card h4,
  .skills-card h4,
  .recent-activity-card h4,
  .stat-row,
  .activity-action,
  .activity-item-name,
  .activity-time,
  .form-group label,
  .stat-item .stat-number,
  .stat-item .stat-label {
    color: #f3f3f3 !important;
  }

  
  .profile-right h3 {
    color: #f3f3f3 !important;
  }

  
  .search-input,
  .filter-select,
  .form-input,
  .form-select,
  .form-textarea {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .search-input:focus,
  .filter-select:focus,
  .form-input:focus,
  .form-select:focus,
  .form-textarea:focus {
    border-color: #0056b3 !important;
  }

  .search-input::placeholder,
  .form-input::placeholder,
  .form-textarea::placeholder {
    color: #aaa !important;
  }

  
  .invite-btn,
  .send-btn {
    background: #0056b3 !important;
    color: #fff !important;
    border-color: #0056b3 !important;
  }

  .invite-btn:hover,
  .send-btn:hover:not(:disabled) {
    background: #004494 !important;
  }

  .view-btn {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .view-btn:hover {
    background: #2a2d2e !important;
  }

  .view-btn.active {
    background: #0056b3 !important;
    color: #fff !important;
    border-color: #0056b3 !important;
  }

  .cancel-btn {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .cancel-btn:hover {
    background: #2a2d2e !important;
  }

  .close-btn {
    color: #f3f3f3 !important;
  }

  .close-btn:hover {
    background: #2a2d2e !important;
  }

  
  .member-role,
  .profile-role,
  .contact-email,
  .stat-value {
    color: #4ea1ff !important;
  }

  .stat-number {
    color: #4ea1ff !important;
  }

  
  .member-card:hover {
    background: #232526 !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
  }

  .stat-card:hover {
    background: #232526 !important;
  }

  
  .skill-tag {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .skill-tag.more {
    background: #0056b3 !important;
    color: #fff !important;
    border-color: #0056b3 !important;
  }

  .skill-badge {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  
  .workload-bar {
    background: #232526 !important;
  }


  
  .member-avatar,
  .large-avatar {
    background: #0056b3 !important;
    color: #fff !important;
  }

  
  .modal-overlay {
    background: rgba(0, 0, 0, 0.7) !important;
  }

  
  .member-list-details {
    border-top-color: #333 !important;
  }

  .modal-header {
    border-bottom-color: #333 !important;
  }

  
  .stat-icon {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }

  
  .search-icon {
    color: #aaa !important;
  }

  
  .social-link {
    color: #4ea1ff !important;
    border-color: #4ea1ff !important;
  }

  .social-link:hover {
    background: #4ea1ff !important;
    color: #fff !important;
  }

  
  .send-btn:disabled {
    background: #444 !important;
    border-color: #444 !important;
    color: #888 !important;
  }

  
  .stats-card,
  .skills-card,
  .recent-activity-card {
    background: #232526 !important;
  }

  .activity-item {
    background: #2a2d2e !important;
    border-color: #444 !important;
  }

  
  .list-stats .list-stat {
    color: #aaa !important;
  }

  
  .team-description,
  .member-location,
  .activity-time,
  .contact-timezone {
    color: #aaa !important;
  }

  
  .member-stats .stat-item .stat-number {
    color: #4ea1ff !important;
  }

  .member-stats .stat-item .stat-label {
    color: #aaa !important;
  }

  
  .workload-percentage[style*="color: #dc3545"] {
    color: #ff6b6b !important;
  }

  .workload-percentage[style*="color: #ffc107"] {
    color: #ffd93d !important;
  }

  .workload-percentage[style*="color: #007bff"] {
    color: #4ea1ff !important;
  }

  .workload-percentage[style*="color: #28a745"] {
    color: #51cf66 !important;
  }

  
  .stat-value[style*="color: #dc3545"] {
    color: #ff6b6b !important;
  }

  .stat-value[style*="color: #ffc107"] {
    color: #ffd93d !important;
  }

  .stat-value[style*="color: #007bff"] {
    color: #4ea1ff !important;
  }

  .stat-value[style*="color: #28a745"] {
    color: #51cf66 !important;
  }
}
</style>