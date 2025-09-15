<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useProjectStore } from '../stores/projectStore'
import { loadStripe } from "@stripe/stripe-js"

const router = useRouter()
const projectStore = useProjectStore()
const projects = computed(() => projectStore.projects)
const selectedProject = computed(() => projectStore.selectedProject)

const searchQuery = ref('')
const searchResults = ref([])
const searchType = ref('') // 'issue' or 'user'
const showRecommendations = ref(false)
const showIssueModal = ref(false)
const showUserModal = ref(false)
const selectedResult = ref(null)
const searchBarRef = ref(null)

// User and project data
const currentUser = ref({
  name: '',
  email: '',
  avatar: '',
  role: '',
  is_premium: false,
  premium_until: null
})

const fetchCurrentUser = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
    }
    const res = await axios.get('/api/me/')
    currentUser.value = {
      name: `${res.data.first_name} ${res.data.last_name}`,
      email: res.data.email,
      avatar: (res.data.first_name[0] || '') + (res.data.last_name[0] || ''),
      role: res.data.role,
      is_premium: res.data.is_premium,
      premium_until: res.data.premium_until
    }
  } catch (e) {
    // Token invalid/expired, force logout
    localStorage.removeItem('token')
    router.push('/login')
  }
}

const fetchProjects = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  try {
    const res = await axios.get('/api/projects/')
    console.log('Fetched projects:', res.data)
    projects.value = res.data
    if (!projectStore.selectedProject && projects.value.length > 0) {
      projectStore.setProject(projects.value[0])
      localStorage.setItem('selectedProjectId', projects.value[0].id)
    }
    const lastId = localStorage.getItem('selectedProjectId')
    if (lastId) {
      const found = projects.value.find(p => p.id === lastId)
      if (found) projectStore.setProject(found)
    }
  } catch (e) {
    // handle error
  }
}

// UI state
const showUserDropdown = ref(false)
const showProjectDropdown = ref(false)
const showCreateDropdown = ref(false)
const notifications = ref(3)

// Menu items
const menuItems = ref([
  { name: 'Home', icon: '🏠', route: '/home', active: false },
  { name: 'Dashboard', icon: '📊', route: '/dashboard', active: true },
  { name: 'Backlog', icon: '📋', route: '/backlog' },
  { name: 'Active Sprint', icon: '🏃', route: '/board' },
  { name: 'Epics', icon: '📚', route: '/epics' },
  { name: 'Sprints', icon: '🔄', route: '/sprints' },
  { name: 'Issues', icon: '🎯', route: '/issues' },
  { name: 'Reports', icon: '📈', route: '/reports' },
  { name: 'Team Members', icon: '👥', route: '/members' },
  { name: 'Settings', icon: '⚙️', route: '/settings' }
])

// Methods
const selectProject = (project) => {
  projectStore.setProject(project)
  showProjectDropdown.value = false
}
const toggleDropdown = (dropdown) => {
  showUserDropdown.value = dropdown === 'user' ? !showUserDropdown.value : false
  showProjectDropdown.value = dropdown === 'project' ? !showProjectDropdown.value : false
  showCreateDropdown.value = dropdown === 'create' ? !showCreateDropdown.value : false
}

const createNew = (type) => {
  console.log('Creating new:', type)
  showCreateDropdown.value = false
  // Handle creation logic here
}

const logout = () => {
  localStorage.removeItem('token');
  router.push('/login')
}

//------------------------------------------------------------AI START------------------------------------------------------------
// AI Assistant methods
// Add these to your Vue component's data/ref section:
const showAIModal = ref(false)
const aiMessage = ref('')
const aiConversation = ref([])
const isAILoading = ref(false)
const aiQuickActions = ref([
  { id: 'priority', label: '🎯 Suggest Task Priority', action: 'getPriorityHelp' },
  { id: 'sprint', label: '🏃 Sprint Planning Advice', action: 'getSprintAdvice' },
  { id: 'insights', label: '📊 Team Performance', action: 'getTeamInsights' },
  { id: 'general', label: '💬 Ask Anything', action: 'openChat' }
])

// Enhanced AI Assistant methods:
const openAIModal = () => {
  showAIModal.value = true
  // Add welcome message if conversation is empty
  if (aiConversation.value.length === 0) {
    aiConversation.value.push({
      role: 'assistant',
      message: '👋 Hi! I\'m your AI project assistant. I can help you with task prioritization, sprint planning, and project insights. What would you like to know?',
      timestamp: new Date().toLocaleTimeString(),
      type: 'welcome'
    })
  }
}

const closeAIModal = () => {
  showAIModal.value = false
  aiMessage.value = ''
}

const sendAIMessage = async () => {
  if (!aiMessage.value.trim()) return
  
  const userMessage = aiMessage.value.trim()
  
  // Add user message to conversation
  aiConversation.value.push({
    role: 'user',
    message: userMessage,
    timestamp: new Date().toLocaleTimeString()
  })
  
  aiMessage.value = ''
  isAILoading.value = true
  
  try {
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
    }

    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/ai/chat/`,
      {
        message: userMessage
      }
    )

    aiConversation.value.push({
      role: 'assistant',
      message: response.data.response,
      timestamp: new Date().toLocaleTimeString(),
      contextUsed: response.data.context_used
    })

  } catch (error) {
    console.error('AI Assistant error:', error)
    aiConversation.value.push({
      role: 'assistant',
      message: 'I\'m having trouble connecting right now. Please try again in a moment.',
      timestamp: new Date().toLocaleTimeString(),
      isError: true
    })
  } finally {
    isAILoading.value = false
    await nextTick()
    // Scroll to bottom of conversation
    scrollToBottom()
  }
}

const handleQuickAction = async (actionType) => {
  isAILoading.value = true
  
  try {
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
    }

    let response
    let message
    
    switch (actionType) {
      case 'getPriorityHelp':
        response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/api/ai/suggest-priority/`)
        message = response.data.suggestion
        aiConversation.value.push({
          role: 'user',
          message: 'Can you help me prioritize my tasks?',
          timestamp: new Date().toLocaleTimeString(),
          isQuickAction: true
        })
        break
        
      case 'getSprintAdvice':
        response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/api/ai/sprint-advice/`)
        message = response.data.advice
        aiConversation.value.push({
          role: 'user',
          message: 'I need advice for sprint planning',
          timestamp: new Date().toLocaleTimeString(),
          isQuickAction: true
        })
        break
        
      case 'getTeamInsights':
        response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/api/ai/team-insights/`)
        message = response.data.insights
        aiConversation.value.push({
          role: 'user',
          message: 'Show me team performance insights',
          timestamp: new Date().toLocaleTimeString(),
          isQuickAction: true
        })
        break
        
      case 'openChat':
        message = 'What would you like to know about your project?'
        break
        
      default:
        message = 'I\'m ready to help! What can I assist you with?'
    }
    
    aiConversation.value.push({
      role: 'assistant',
      message: message,
      timestamp: new Date().toLocaleTimeString()
    })

  } catch (error) {
    console.error('Quick action error:', error)
    aiConversation.value.push({
      role: 'assistant',
      message: 'I couldn\'t complete that action right now. Please try asking me directly!',
      timestamp: new Date().toLocaleTimeString(),
      isError: true
    })
  } finally {
    isAILoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  const conversationElement = document.querySelector('.ai-conversation')
  if (conversationElement) {
    conversationElement.scrollTop = conversationElement.scrollHeight
  }
}

const clearConversation = () => {
  aiConversation.value = []
  openAIModal() // This will add the welcome message again
}

const handleAIKeyPress = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendAIMessage()
  }
}
//------------------------------------------------------------AI END------------------------------------------------------------

// Close dropdowns when clicking outside
const closeDropdowns = () => {
  showUserDropdown.value = false
  showProjectDropdown.value = false
  showCreateDropdown.value = false
}

const autoCompleteSprints = async () => {
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  await axios.post('/api/sprints/auto-complete/')
}

const buyPremium = async () => {
  try {
    const stripe = await loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)

    // Token do autoryzacji (jak w innych requestach)
    const token = localStorage.getItem("token")
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Token ${token}`
    }

    // Wywołanie backendu
    const res = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/payments/create-checkout-session/`
    )

    const sessionId = res.data.id
    const { error } = await stripe.redirectToCheckout({ sessionId })

    if (error) {
      console.error("Stripe checkout error:", error)
    }
  } catch (e) {
    console.error("Error creating checkout session", e)
  }
}

function formatPremiumDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const searchIssues = async () => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query || !selectedProject.value?.id) return

  // Search issues
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const issuesRes = await axios.get(`/api/projects/${selectedProject.value.id}/issues/`)
  const usersRes = await axios.get(`/api/projects/${selectedProject.value.id}/users/`)

  // Filter issues
  const issues = issuesRes.data.filter(issue =>
    (issue.title && issue.title.toLowerCase().includes(query)) ||
    (issue.key && issue.key.toLowerCase().includes(query))
  )
  // Filter users
  const users = usersRes.data.filter(user =>
    (user.first_name && user.first_name.toLowerCase().includes(query)) ||
    (user.last_name && user.last_name.toLowerCase().includes(query)) ||
    (user.email && user.email.toLowerCase().includes(query))
  )

  if (issues.length > 0) {
    searchResults.value = issues
    searchType.value = 'issue'
    showIssueModal.value = true
    showUserModal.value = false
  } else if (users.length > 0) {
    searchResults.value = users
    searchType.value = 'user'
    showUserModal.value = true
    showIssueModal.value = false
  } else {
    searchResults.value = []
    searchType.value = ''
    showIssueModal.value = false
    showUserModal.value = false
    alert('No results found.')
  }
}

// When a result is clicked, show the modal for that item
const openResultModal = (item) => {
  selectedResult.value = item
  if (searchType.value === 'issue') {
    showIssueModal.value = true
  } else if (searchType.value === 'user') {
    showUserModal.value = true
  }
}

// When a recommendation is clicked
const selectRecommendation = (item) => {
  selectedResult.value = item
  showRecommendations.value = false
  if (item._type === 'issue') {
    showIssueModal.value = true
  } else if (item._type === 'user') {
    showUserModal.value = true
  }
}

const closeModals = () => {
  showIssueModal.value = false
  showUserModal.value = false
  selectedResult.value = null
}

onMounted(() => {
  document.addEventListener('click', closeDropdowns)
  fetchCurrentUser()
  projectStore.fetchProjects()
  autoCompleteSprints()
  document.addEventListener('click', (e) => {
    if (!searchBarRef.value?.contains(e.target)) {
      showRecommendations.value = false
    }
  })
})

// Live search as you type
watch(searchQuery, async (newQuery) => {
  if (!newQuery || !selectedProject.value?.id) {
    searchResults.value = []
    showRecommendations.value = false
    return
  }
  const query = newQuery.trim().toLowerCase()
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  // Fetch issues and users in parallel
  const [issuesRes, usersRes] = await Promise.all([
    axios.get(`/api/projects/${selectedProject.value.id}/issues/`),
    axios.get(`/api/projects/${selectedProject.value.id}/users/`)
  ])
  // Filter issues
  const issues = issuesRes.data.filter(issue =>
    (issue.title && issue.title.toLowerCase().includes(query)) ||
    (issue.key && issue.key.toLowerCase().includes(query))
  )
  // Filter users
  const users = usersRes.data.filter(user =>
    (user.first_name && user.first_name.toLowerCase().includes(query)) ||
    (user.last_name && user.last_name.toLowerCase().includes(query)) ||
    (user.email && user.email.toLowerCase().includes(query))
  )
  // Combine and tag results
  searchResults.value = [
    ...issues.map(i => ({ ...i, _type: 'issue' })),
    ...users.map(u => ({ ...u, _type: 'user' }))
  ]
  showRecommendations.value = searchResults.value.length > 0
})
</script>

<template>
  <div class="dashboard-layout" @click="closeDropdowns">
    <!-- Top Navigation Bar -->
    <header class="top-nav">
      <div class="nav-left">
        <!-- Logo -->
        <div class="logo">
          <span class="logo-icon">🎯</span>
          <span class="logo-text">TaskFlow</span>
        </div>

        <!-- Project Selector -->
        <div class="project-selector" @click.stop>
          <button 
            class="project-btn" 
            @click="toggleDropdown('project')"
            :class="{ active: showProjectDropdown }"
          >
            <span class="project-key">{{ selectedProject?.key }}</span>
            <span class="project-name">{{ selectedProject?.name }}</span>
            <span class="dropdown-arrow">▼</span>
          </button>
          <div v-if="showProjectDropdown" class="dropdown project-dropdown">
            <div v-for="project in projects" :key="project.id" class="dropdown-item" @click="selectProject(project)">
                <span class="project-key">{{ project.key }}</span>
                <span class="project-name">{{ project.name }}</span>
            </div>
            <div v-if="projects.length === 0" style="padding:1rem;color:#888;">No projects found</div>
          </div>
        </div>

        <!-- Quick Create Button -->
        <div class="quick-create" @click.stop>
          <button class="create-btn" @click="router.push('/create-project')">
            + Create Project
          </button>
        </div>
      </div>

      <div class="nav-center">
        <!-- Search Bar -->
        <div class="search-bar" ref="searchBarRef" style="position:relative;">
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Search issues, epics, users..."
            @focus="showRecommendations = searchResults.length > 0"
          />
          <button class="search-btn" @click="showRecommendations = searchResults.length > 0">🔍</button>
          <!-- Recommendations Dropdown -->
          <div v-if="showRecommendations" class="search-dropdown">
            <div 
              v-for="item in searchResults.slice(0, 8)" 
              :key="item.id + item._type"
              class="search-result"
              @mousedown.prevent="selectRecommendation(item)"
            >
              <template v-if="item._type === 'issue'">
                <span class="result-type">🎯 Issue</span>
                <strong>{{ item.key }}</strong>: {{ item.title }}
              </template>
              <template v-else>
                <span class="result-type">👤 User</span>
                {{ item.first_name }} {{ item.last_name }} ({{ item.email }})
              </template>
            </div>
            <div v-if="searchResults.length === 0" class="search-no-results">No results found.</div>
          </div>
        </div>
        <!-- Issue Modal -->
        <div v-if="showIssueModal && selectedResult" class="modal-overlay" @click.self="closeModals">
          <div class="modal-content">
            <h4>{{ selectedResult.key }}: {{ selectedResult.title }}</h4>
            <p>{{ selectedResult.description }}</p>
            <p><strong>Status:</strong> {{ selectedResult.status }}</p>
            <p><strong>Assignee:</strong> {{ selectedResult.assignee }}</p>
            <p><strong>Story Points:</strong> {{ selectedResult.story_points }}</p>
            <button @click="closeModals">Close</button>
          </div>
        </div>
        <!-- User Modal -->
        <div v-if="showUserModal && selectedResult" class="modal-overlay" @click.self="closeModals">
          <div class="modal-content">
            <h4>{{ selectedResult.first_name }} {{ selectedResult.last_name }}</h4>
            <p>Email: {{ selectedResult.email }}</p>
            <p>Role: {{ selectedResult.role }}</p>
            <button @click="closeModals">Close</button>
          </div>
        </div>
      </div>

      <div class="nav-right">
        <!-- Notifications -->
          <button @click="buyPremium" class="create-btn">
            Buy Premium
          </button>
          <span v-if="currentUser.is_premium" style="color: #28a745; font-weight: bold;">
            Premium until {{ formatPremiumDate(currentUser.premium_until) }}
          </span>
        <button class="notification-btn">
          🔔
          <span v-if="notifications > 0" class="notification-badge">{{ notifications }}</span>
        </button>

        <!-- User Menu -->
        <div class="user-menu" @click.stop>
          <button 
            class="user-btn"
            @click="toggleDropdown('user')"
            :class="{ active: showUserDropdown }"
          >
            <div class="user-avatar">{{ currentUser.avatar }}</div>
            <span class="dropdown-arrow">▼</span>
          </button>
          
          <div v-if="showUserDropdown" class="dropdown user-dropdown">
            <div class="user-info">
              <div class="user-name">{{ currentUser.name }}</div>
              <div class="user-email">{{ currentUser.email }}</div>
            </div>
            <hr>
            <div class="dropdown-item">👤 Profile</div>
            <div class="dropdown-item" @click="router.push('/settings')">⚙️ Settings</div>
            <hr>
            <div class="dropdown-item" @click="logout">🚪 Logout</div>
          </div>
        </div>
      </div>
    </header>

    <div class="main-layout">
      <!-- Sidebar -->
      <nav class="sidebar">
        <div class="sidebar-content">
          <div class="menu-items">
            <router-link 
              v-for="item in menuItems" 
              :key="item.name"
              :to="item.route"
              class="menu-item"
              :class="{ active: $route.path === item.route }"
            >
              <span class="menu-icon">{{ item.icon }}</span>
              <span class="menu-text">{{ item.name }}</span>
            </router-link>
          </div>
          
          <!-- AI Assistant Button at the bottom -->
          <div class="sidebar-bottom">
            <button class="ai-assistant-btn" @click="openAIModal">
              <span class="menu-icon">🤖</span>
              <span class="menu-text">Ask AI Assistant</span>
            </button>
          </div>
        </div>
      </nav>

      <!-- Main Content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- AI Assistant Modal -->
    <div v-if="showAIModal" class="modal-overlay" @click.self="closeAIModal">
      <div class="ai-modal-content">
        <div class="ai-modal-header">
          <h3>🤖 AI Project Assistant</h3>
          <div class="ai-header-actions">
            <button class="clear-btn" @click="clearConversation" title="Clear conversation">
              🗑️
            </button>
            <button class="close-btn" @click="closeAIModal">✕</button>
          </div>
        </div>
        
        <!-- Quick Actions -->
        <div v-if="aiConversation.length <= 1" class="ai-quick-actions">
          <h4>Quick Actions:</h4>
          <div class="quick-action-buttons">
            <button 
              v-for="action in aiQuickActions" 
              :key="action.id"
              @click="handleQuickAction(action.action)"
              class="quick-action-btn"
              :disabled="isAILoading"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
        
        <!-- Conversation Area -->
        <div class="ai-conversation" id="ai-conversation">
          <div 
            v-for="(msg, index) in aiConversation" 
            :key="index" 
            class="message" 
            :class="[msg.role, { 'error-message': msg.isError, 'quick-action': msg.isQuickAction }]"
          >
            <div class="message-content">
              <div class="message-text">
                {{ msg.message }}
                <span v-if="msg.contextUsed" class="context-indicator" title="Response used your project data">
                  📊
                </span>
              </div>
              <div class="message-time">{{ msg.timestamp }}</div>
            </div>
          </div>
          
          <!-- Loading indicator -->
          <div v-if="isAILoading" class="message assistant">
            <div class="message-content">
              <div class="message-text">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Input Area -->
        <div class="ai-input-area">
          <div class="input-with-suggestions">
            <textarea 
              v-model="aiMessage"
              placeholder="Ask about tasks, sprints, team performance, or anything project-related..."
              class="ai-input"
              @keypress="handleAIKeyPress"
              rows="3"
            ></textarea>
            <div class="input-suggestions">
              <span class="suggestion-chip" @click="aiMessage = 'What should I work on next?'">
                What should I work on next?
              </span>
              <span class="suggestion-chip" @click="aiMessage = 'How is my team performing?'">
                How is my team performing?
              </span>
              <span class="suggestion-chip" @click="aiMessage = 'Help me plan the next sprint'">
                Help me plan the next sprint
              </span>
            </div>
          </div>
          <button 
            @click="sendAIMessage" 
            class="send-btn"
            :disabled="!aiMessage.trim() || isAILoading"
          >
            <span v-if="!isAILoading">Send</span>
            <span v-else>...</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: #f8f9fa;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

/* Top Navigation */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #e1e5e9;
  padding: 0 1rem;
  height: 60px;
  position: relative;
  z-index: 100;
  flex-shrink: 0;
  width: 100%;
  margin-right: auto;
}

.nav-left, .nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 400px;
  margin: 0 2rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: bold;
  color: #0066cc;
}

.logo-icon {
  font-size: 1.5rem;
}

.project-selector {
  position: relative;
}

.project-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.project-btn:hover, .project-btn.active {
  background: #e9ecef;
  border-color: #0066cc;
}

.project-key {
  background: #0066cc;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: bold;
}

.create-btn {
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-btn:hover, .create-btn.active {
  background: #0056b3;
}

.search-bar {
  display: flex;
  width: 100%;
  max-width: 400px;
}

.search-bar input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-right: none;
  border-radius: 4px 0 0 4px;
  outline: none;
}

.search-bar input:focus {
  border-color: #0066cc;
}

.search-btn {
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-left: none;
  border-radius: 0 4px 4px 0;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
}

.notification-btn {
  position: relative;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.notification-btn:hover {
  background: #f8f9fa;
}

.notification-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
  margin-right: 1rem;
}

.user-btn:hover, .user-btn.active {
  background: #f8f9fa;
}

.user-avatar {
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

/* Dropdowns */
.dropdown {
  position: absolute;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 200px;
}

.project-dropdown, .create-dropdown {
  top: 100%;
  left: 0;
  margin-top: 0.25rem;
}

.user-dropdown {
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
}

.dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dropdown-item:hover {
  background: #f8f9fa;
}

.user-info {
  padding: 0.75rem 1rem;
}

.user-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.9rem;
  color: #666;
}

/* Main Layout */
.main-layout {
  display: flex;
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 250px;
  background: white;
  border-right: 1px solid #e1e5e9;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.menu-items {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0 0.5rem;
  border-radius: 4px;
  text-decoration: none;
  color: inherit;
}

.menu-item:hover {
  background: #f8f9fa;
}

.menu-item.active {
  background: #e3f2fd;
  color: #0066cc;
  font-weight: 500;
}

.menu-icon {
  font-size: 1.1rem;
}

.sidebar-bottom {
  border-top: 1px solid #e1e5e9;
  padding: 1rem 0.5rem;
}

.ai-assistant-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.ai-assistant-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.ai-assistant-btn:active {
  transform: translateY(0);
}

/* Main Content */
.main-content {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  padding: 2rem;
  overflow-y: auto;
  height: 100%;
  margin-right: 1rem;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.project-description {
  color: #666;
  margin: 0;
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.dashboard-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-card h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

/* Progress Bar */
.progress-container {
  margin-top: 1rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #28a745;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9rem;
  color: #666;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #0066cc;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
}

/* Activity Card */
.activity-card {
  grid-column: span 2;
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
  background: #f8f9fa;
  border-radius: 4px;
}

.activity-content {
  flex: 1;
}

.activity-user {
  font-weight: 500;
  color: #0066cc;
}

.activity-action {
  margin: 0 0.25rem;
  color: #666;
}

.activity-item-name {
  font-weight: 500;
}

.activity-time {
  font-size: 0.9rem;
  color: #999;
  white-space: nowrap;
}

.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal-content {
  background: #fff; padding: 2rem; border-radius: 8px; min-width: 300px; max-width: 90vw;
}
.search-dropdown {
  position: absolute;
  top: 110%;
  left: 0;
  width: 100%;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 0 0 6px 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
}
.search-result {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #f1f1f1;
  transition: background 0.2s;
}
.search-result:last-child {
  border-bottom: none;
}
.search-result:hover {
  background: #f3f8ff;
}
.result-type {
  font-size: 0.8em;
  color: #888;
  margin-right: 0.5em;
}
.search-no-results {
  padding: 0.75rem 1rem;
  color: #888;
}

/* AI Assistant Modal Styles */
.ai-modal-content {
  background: white;
  border-radius: 12px;
  width: 90vw;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.ai-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e1e5e9;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.ai-conversation {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  max-height: 50vh;
}

.ai-welcome {
  text-align: center;
  color: #666;
  margin-bottom: 2rem;
}

.ai-welcome h4 {
  color: #333;
  margin-bottom: 1rem;
}

.ai-welcome ul {
  text-align: left;
  max-width: 300px;
  margin: 1rem auto;
}

.ai-welcome li {
  margin-bottom: 0.5rem;
}

.message {
  margin-bottom: 1rem;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 18px;
  position: relative;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 6px;
}

.message.assistant .message-content {
  background: #f1f3f5;
  color: #333;
  border-bottom-left-radius: 6px;
}

.message-text {
  line-height: 1.4;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 0.5rem;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #999;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.ai-input-area {
  padding: 1.5rem;
  border-top: 1px solid #e1e5e9;
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.ai-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 20px;
  resize: none;
  outline: none;
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.4;
}

.ai-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.send-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.ai-modal-content {
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.ai-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e1e5e9;
}

.ai-header-actions {
  display: flex;
  gap: 0.5rem;
}

.clear-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
}

.clear-btn:hover {
  background: #f3f4f6;
}

.ai-quick-actions {
  padding: 1rem;
  border-bottom: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.quick-action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.quick-action-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.quick-action-btn:hover:not(:disabled) {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.quick-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-conversation {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  max-height: 400px;
}

.message.error-message .message-text {
  color: #dc3545;
  background: #f8d7da;
  border-left: 3px solid #dc3545;
  padding-left: 0.75rem;
}

.message.quick-action {
  opacity: 0.8;
  font-style: italic;
}

.context-indicator {
  margin-left: 0.5rem;
  font-size: 0.8rem;
}

.input-with-suggestions {
  flex: 1;
  position: relative;
}

.input-suggestions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.suggestion-chip {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.2s;
}

.suggestion-chip:hover {
  background: #007bff;
  color: white;
}

.ai-input-area {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-top: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #007bff;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

/* Responsive */
@media (max-width: 768px) {
  .nav-center {
    display: none;
  }
  
  .sidebar {
    width: 200px;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .activity-card {
    grid-column: span 1;
  }

  .ai-modal-content {
    width: 95vw;
    max-height: 90vh;
  }

  .ai-conversation {
    max-height: 40vh;
  }

  .message-content {
    max-width: 90%;
  }
}

/* Dark Mode Styles */
@media (prefers-color-scheme: dark) {
  .dashboard-layout {
    background-color: #181a1b !important;
  }

  /* Top Navigation */
  .top-nav {
    background: #232526 !important;
    border-bottom: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .logo {
    color: #4ea1ff !important;
  }

  .logo-text {
    color: #f3f3f3 !important;
  }

  /* Project Selector */
  .project-btn {
    background: #181a1b !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .project-btn:hover, .project-btn.active {
    background: #232526 !important;
    border-color: #4ea1ff !important;
  }

  .project-key {
    background: #0056b3 !important;
    color: #fff !important;
  }

  .project-name {
    color: #f3f3f3 !important;
  }

  /* Create Button */
  .create-btn {
    background: #0056b3 !important;
    color: #fff !important;
  }

  .create-btn:hover, .create-btn.active {
    background: #004494 !important;
  }

  /* Search Bar */
  .search-bar input {
    background: #181a1b !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .search-bar input:focus {
    border-color: #4ea1ff !important;
  }

  .search-bar input::placeholder {
    color: #aaa !important;
  }

  .search-btn {
    background: #232526 !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .search-btn:hover {
    background: #333 !important;
  }

  /* Notification Button */
  .notification-btn {
    color: #f3f3f3 !important;
  }

  .notification-btn:hover {
    background: #232526 !important;
  }

  .notification-badge {
    background: #e74c3c !important;
    color: #fff !important;
  }

  /* User Menu */
  .user-btn {
    color: #f3f3f3 !important;
  }

  .user-btn:hover, .user-btn.active {
    background: #232526 !important;
  }

  .user-avatar {
    background: #0056b3 !important;
    color: #fff !important;
  }

  /* Dropdowns */
  .dropdown {
    background: #232526 !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .dropdown-item {
    color: #f3f3f3 !important;
  }

  .dropdown-item:hover {
    background: #181a1b !important;
  }

  .user-info .user-name {
    color: #f3f3f3 !important;
  }

  .user-info .user-email {
    color: #aaa !important;
  }

  /* Sidebar */
  .sidebar {
    background: #232526 !important;
    border-right: 1px solid #444 !important;
  }

  .sidebar-bottom {
    border-top: 1px solid #444 !important;
  }

  .menu-item {
    color: #f3f3f3 !important;
  }

  .menu-item:hover {
    background: #181a1b !important;
  }

  .menu-item.active {
    background: #1a3a52 !important;
    color: #4ea1ff !important;
  }

  /* Main Content */
  .main-content {
    background: #181a1b !important;
    color: #f3f3f3 !important;
  }

  /* Dashboard Cards */
  .dashboard-card {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .dashboard-card h3 {
    color: #f3f3f3 !important;
  }

  /* Progress Bar */
  .progress-bar {
    background: #333 !important;
  }

  .progress-fill {
    background: #28a745 !important;
  }

  .progress-text {
    color: #aaa !important;
  }

  /* Stats */
  .stat-number {
    color: #4ea1ff !important;
  }

  .stat-label {
    color: #aaa !important;
  }

  /* Activity Items */
  .activity-item {
    background: #181a1b !important;
    color: #f3f3f3 !important;
  }

  .activity-user {
    color: #4ea1ff !important;
  }

  .activity-action {
    color: #aaa !important;
  }

  .activity-item-name {
    color: #f3f3f3 !important;
  }

  .activity-time {
    color: #888 !important;
  }

  /* Dashboard Header */
  .dashboard-header h1 {
    color: #f3f3f3 !important;
  }

  .project-description {
    color: #aaa !important;
  }

  /* Dropdown Arrow */
  .dropdown-arrow {
    color: #f3f3f3 !important;
  }

  /* HR elements */
  hr {
    border-color: #444 !important;
  }
  /* Modal Overlay */
  .modal-overlay {
    background: rgba(0, 0, 0, 0.8) !important;
  }

  .modal-content {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }

  /* Search Dropdown */
  .search-dropdown {
    background: #232526 !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .search-result {
    color: #f3f3f3 !important;
    border-bottom: 1px solid #444 !important;
  }

  .search-result:hover {
    background: #1a3a52 !important;
  }

  .result-type {
    color: #aaa !important;
  }

  .search-no-results {
    color: #aaa !important;
  }

  /* AI Modal Dark Mode */
  .ai-modal-content {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }

  .ai-modal-header {
    border-bottom: 1px solid #444 !important;
  }

  .ai-conversation {
    background: #232526 !important;
  }

  .ai-welcome {
    color: #aaa !important;
  }

  .ai-welcome h4 {
    color: #f3f3f3 !important;
  }

  .message.assistant .message-content {
    background: #181a1b !important;
    color: #f3f3f3 !important;
  }

  .ai-input-area {
    border-top: 1px solid #444 !important;
    background: #232526 !important;
  }

  .ai-input {
    background: #181a1b !important;
    border: 1px solid #444 !important;
    color: #f3f3f3 !important;
  }

  .ai-input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
  }

  .ai-input::placeholder {
    color: #aaa !important;
  }

  .typing-indicator span {
    background: #aaa !important;
  }
}
</style>