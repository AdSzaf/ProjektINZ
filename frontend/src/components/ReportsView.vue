<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import axios from 'axios'

// Report data
const selectedTimeframe = ref('current-sprint')
const selectedReport = ref('burndown')
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.selectedProject)

const sprintInfo = ref(null)
const burndownData = ref([])
const velocityData = ref([])
const issueBreakdown = ref({})
const teamPerformance = ref([])
const sprintIssues = ref([])

const timeframeOptions = [
  { value: 'current-sprint', label: 'Current Sprint' },
  { value: 'last-sprint', label: 'Last Sprint' },
  { value: 'last-30-days', label: 'Last 30 Days' },
  { value: 'last-quarter', label: 'Last Quarter' }
]

const reportTypes = [
  { value: 'burndown', label: 'Burndown Chart', icon: '📉' },
  { value: 'velocity', label: 'Velocity Chart', icon: '🚀' },
  { value: 'cumulative', label: 'Cumulative Flow', icon: '📊' },
  { value: 'time-tracking', label: 'Time Tracking', icon: '⏱️' }
]

const totalStoryPoints = computed(() => {
  return sprintIssues.value.reduce((sum, issue) => sum + (issue.story_points || 0), 0)
})

const completedStoryPoints = computed(() => {
  return sprintIssues.value
    .filter(issue => issue.status && issue.status.toLowerCase() === 'done')
    .reduce((sum, issue) => sum + (issue.story_points || 0), 0)
})

// Computed properties
const sprintProgressPercentage = computed(() => {
  if (!totalStoryPoints.value) return 0
  return Math.round((completedStoryPoints.value / totalStoryPoints.value) * 100)
})

const remainingDays = computed(() => {
  if (!sprintInfo.value) return 0
  const today = new Date()
  const end = new Date(sprintInfo.value.end_date)
  const diff = Math.ceil((end - today) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 0
})

const averageVelocity = computed(() => {
  const total = velocityData.value.reduce((sum, sprint) => sum + sprint.completed, 0)
  return Math.round(total / velocityData.value.length)
})

const maxBurndownValue = computed(() => {
  const values = burndownData.value.map(d => Math.max(d.ideal, d.actual))
  const max = Math.max(...values)
  return isFinite(max) && max > 0 ? max : 1
})

// Chart drawing functions
const drawBurndownChart = () => {
  const canvas = document.getElementById('burndown-canvas')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  // Clear canvas
  ctx.clearRect(0, 0, width, height)
  
  // Chart dimensions
  const padding = 40
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding
  
  // Scales
  const xScale = chartWidth / (burndownData.value.length - 1)
  const yScale = chartHeight / maxBurndownValue.value
  
  // Draw grid lines
  ctx.strokeStyle = '#e9ecef'
  ctx.lineWidth = 1
  
  // Horizontal grid lines
  for (let i = 0; i <= 5; i++) {
    const y = padding + (chartHeight / 5) * i
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()
  }
  
  // Vertical grid lines
  for (let i = 0; i < burndownData.value.length; i += 2) {
    const x = padding + xScale * i
    ctx.beginPath()
    ctx.moveTo(x, padding)
    ctx.lineTo(x, height - padding)
    ctx.stroke()
  }
  
  // Draw ideal line
  ctx.strokeStyle = '#6c757d'
  ctx.lineWidth = 2
  ctx.setLineDash([5, 5])
  ctx.beginPath()
  burndownData.value.forEach((point, index) => {
    const x = padding + xScale * index
    const y = height - padding - (point.ideal * yScale)
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()
  
  // Draw actual line
  ctx.strokeStyle = '#007bff'
  ctx.lineWidth = 3
  ctx.setLineDash([])
  ctx.beginPath()
  burndownData.value.forEach((point, index) => {
    const x = padding + xScale * index
    const y = height - padding - (point.actual * yScale)
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()
  
  // Draw data points
  burndownData.value.forEach((point, index) => {
    const x = padding + xScale * index
    const actualY = height - padding - (point.actual * yScale)
    
    // Actual points
    ctx.fillStyle = '#007bff'
    ctx.beginPath()
    ctx.arc(x, actualY, 4, 0, 2 * Math.PI)
    ctx.fill()
  })
  
  // Draw labels
  ctx.fillStyle = '#333'
  ctx.font = '12px Arial'
  ctx.textAlign = 'center'
  
  // Y-axis labels
  ctx.textAlign = 'right'
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((maxBurndownValue.value / 5) * (5 - i))
    const y = padding + (chartHeight / 5) * i + 4
    ctx.fillText(value.toString(), padding - 10, y)
  }
  
  // X-axis labels (show every 2nd day)
  ctx.textAlign = 'center'
  for (let i = 0; i < burndownData.value.length; i += 2) {
    const x = padding + xScale * i
    const date = new Date(burndownData.value[i].date)
    const label = `${date.getMonth() + 1}/${date.getDate()}`
    ctx.fillText(label, x, height - padding + 20)
  }
}

const drawVelocityChart = () => {
  const canvas = document.getElementById('velocity-canvas')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  
  // Set canvas size properly
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
  
  const width = canvas.width
  const height = canvas.height
  
  ctx.clearRect(0, 0, width, height)
  
  if (!velocityData.value.length) {
    // Show "No data" message
    ctx.fillStyle = '#666'
    ctx.font = '16px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('No velocity data available', width / 2, height / 2)
    return
  }
  
  const padding = 40
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding
  const barWidth = (chartWidth / velocityData.value.length) * 0.6
  const barSpacing = (chartWidth / velocityData.value.length) * 0.4
  
  const maxValue = Math.max(...velocityData.value.map(d => Math.max(d.planned, d.completed)))
  const yScale = chartHeight / maxValue
  
  // Draw grid lines
  ctx.strokeStyle = '#e9ecef'
  ctx.lineWidth = 1
  
  // Horizontal grid lines
  for (let i = 0; i <= 5; i++) {
    const y = padding + (chartHeight / 5) * i
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()
  }
  
  // Draw Y-axis labels
  ctx.fillStyle = '#666'
  ctx.font = '12px Arial'
  ctx.textAlign = 'right'
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((maxValue / 5) * (5 - i))
    const y = padding + (chartHeight / 5) * i + 4
    ctx.fillText(value.toString(), padding - 10, y)
  }
  
  // Draw bars
  velocityData.value.forEach((sprint, index) => {
    const x = padding + (chartWidth / velocityData.value.length) * index + (barSpacing / 2)
    
    // Planned bar (background)
    const plannedHeight = sprint.planned * yScale
    ctx.fillStyle = '#e9ecef'
    ctx.fillRect(x, height - padding - plannedHeight, barWidth, plannedHeight)
    
    // Completed bar (foreground)
    const completedHeight = sprint.completed * yScale
    ctx.fillStyle = index === velocityData.value.length - 1 ? '#007bff' : '#28a745'
    ctx.fillRect(x, height - padding - completedHeight, barWidth, completedHeight)
    
    // Sprint labels
    ctx.fillStyle = '#333'
    ctx.font = '12px Arial'
    ctx.textAlign = 'center'
    
    // Draw label rotated
    ctx.save()
    ctx.translate(x + barWidth / 2, height - padding + 20)
    ctx.rotate(-Math.PI / 6) // 30 degrees instead of 45
    ctx.fillText(sprint.sprint.replace('Sprint ', 'S'), 0, 0)
    ctx.restore()
    
    // Draw values on bars
    ctx.fillStyle = '#333'
    ctx.font = '11px Arial'
    ctx.textAlign = 'center'
    
    // Completed value
    if (completedHeight > 20) {
      ctx.fillText(sprint.completed.toString(), x + barWidth / 2, height - padding - completedHeight / 2 + 3)
    }
    
    // Planned value (if different from completed)
    if (sprint.planned !== sprint.completed && plannedHeight > 20) {
      ctx.fillStyle = '#666'
      ctx.fillText(sprint.planned.toString(), x + barWidth / 2, height - padding - plannedHeight + 15)
    }
  })
  
  // Draw axes
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 2
  
  // Y-axis
  ctx.beginPath()
  ctx.moveTo(padding, padding)
  ctx.lineTo(padding, height - padding)
  ctx.stroke()
  
  // X-axis
  ctx.beginPath()
  ctx.moveTo(padding, height - padding)
  ctx.lineTo(width - padding, height - padding)
  ctx.stroke()
}

const fetchSprintInfo = async () => {
   if (!currentProject.value || !currentProject.value.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  // Get current sprint for the project
  const res = await axios.get(`/api/projects/${currentProject.value.id}/sprints/?status=active`)
  sprintInfo.value = res.data[0] || null
  console.log('Fetched sprint info:', sprintInfo.value)
}

const fetchBurndownData = async () => {
  if (!currentProject.value || !currentProject.value.id) return
  if (!sprintInfo.value) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  // Get burndown data for current sprint
  const res = await axios.get(`/api/sprints/${sprintInfo.value.id}/burndown/`)
  burndownData.value = res.data
  console.log('Fetched burndown data:', burndownData.value)
}

const fetchVelocityData = async () => {
  if (!currentProject.value || !currentProject.value.id) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  // Get velocity for last N sprints
  const res = await axios.get(`/api/projects/${currentProject.value.id}/velocity/`)
  velocityData.value = res.data
  console.log('Fetched velocity data:', velocityData.value)
}

const fetchIssueBreakdown = async () => {
  if (!currentProject.value || !currentProject.value.id) return
  if (!sprintInfo.value) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  // Get issue breakdown for current sprint
  const res = await axios.get(`/api/sprints/${sprintInfo.value.id}/breakdown/`)
  issueBreakdown.value = res.data
  console.log('Fetched issue breakdown:', issueBreakdown.value)
}

const fetchTeamPerformance = async () => {
  if (!currentProject.value || !currentProject.value.id) return
  if (!sprintInfo.value) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  // Get team performance for current sprint
  const res = await axios.get(`/api/sprints/${sprintInfo.value.id}/team-performance/`)
  teamPerformance.value = res.data
  console.log('Fetched team performance:', teamPerformance.value)
}

const fetchSprintIssues = async () => {
  if (!currentProject.value || !currentProject.value.id) return
  if (!sprintInfo.value) return
  const token = localStorage.getItem('token')
  axios.defaults.headers.common['Authorization'] = `Token ${token}`
  const res = await axios.get(`/api/projects/${currentProject.value.id}/issues/`)
  // Filter issues for the current sprint
  sprintIssues.value = res.data.filter(issue => issue.sprint === sprintInfo.value.id)
  console.log('Fetched sprint issues:', sprintIssues.value)
}

const renderActiveChart = () => {
  nextTick(() => {
    setTimeout(() => {
      if (selectedReport.value === 'burndown' && burndownData.value.length > 0) {
        const canvas = document.getElementById('burndown-canvas')
        if (canvas) {
          drawBurndownChart()
        }
      } else if (selectedReport.value === 'velocity' && velocityData.value.length > 0) {
        const canvas = document.getElementById('velocity-canvas')
        if (canvas && canvas.offsetWidth > 0) {
          canvas.width = canvas.offsetWidth
          canvas.height = canvas.offsetHeight
          drawVelocityChart()
        }
      }
    }, 10)
  })
}

onMounted(async () => {

  await fetchSprintInfo()
  await fetchSprintIssues()
  await fetchBurndownData()
  await fetchVelocityData()
  await fetchIssueBreakdown()
  await fetchTeamPerformance()
  
  renderActiveChart()
})

watch(currentProject, async (newVal) => {
  if (newVal && newVal.id) {
    await fetchSprintInfo()
    await fetchSprintIssues()
    await fetchBurndownData()
    await fetchVelocityData()
    await fetchIssueBreakdown()
    await fetchTeamPerformance()

    renderActiveChart()
  }
}, { immediate: true })

watch(selectedReport, () => {
   renderActiveChart()
})

watch(burndownData, (newVal) => {
  if (newVal && newVal.length > 0 && selectedReport.value === 'burndown') {
    renderActiveChart()
  }
})

watch(velocityData, (newVal) => {
  if (newVal && newVal.length > 0 && selectedReport.value === 'velocity') {
    renderActiveChart()
  }
})
</script>

<template>
  <div class="reports-container">
    <!-- Reports Header -->
    <div class="reports-header">
      <h1>Reports & Analytics</h1>
      <p class="reports-description">Track progress, analyze team performance, and monitor project health</p>
      
      <!-- Report Controls -->
      <div class="report-controls">
        <div class="control-group">
          <label>Time Frame:</label>
          <select v-model="selectedTimeframe" class="control-select">
            <option v-for="option in timeframeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
        
        <div class="control-group">
          <label>Report Type:</label>
          <select v-model="selectedReport" class="control-select">
            <option v-for="report in reportTypes" :key="report.value" :value="report.value">
              {{ report.icon }} {{ report.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Sprint Overview -->
    <div class="sprint-overview" v-if="sprintInfo">
      <div class="overview-card">
        <h3>{{ sprintInfo?.name }} Overview</h3>
        <div class="overview-stats">
          <div class="stat">
            <span class="stat-label">Progress</span>
            <span class="stat-value">{{ sprintProgressPercentage }}%</span>
          </div>
          <div class="stat">
            <span class="stat-label">Completed</span>
            <span class="stat-value">{{ completedStoryPoints }}/{{ totalStoryPoints }} SP</span>
          </div>
          <div class="stat">
            <span class="stat-label">Days Left</span>
            <span class="stat-value">{{ remainingDays }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Avg Velocity</span>
            <span class="stat-value">{{ averageVelocity }} SP</span>
          </div>
        </div>
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: sprintProgressPercentage + '%' }"></div>
          </div>
          <div class="progress-text">{{ completedStoryPoints }} of {{ totalStoryPoints }} story points completed</div>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Burndown Chart -->
      <div class="chart-card" v-show="selectedReport === 'burndown'">
        <div class="chart-header">
          <h3>📉 Burndown Chart</h3>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-color ideal"></span>
              Ideal
            </span>
            <span class="legend-item">
              <span class="legend-color actual"></span>
              Actual
            </span>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="burndown-canvas" width="800" height="400"></canvas>
        </div>
      </div>

      <!-- Velocity Chart -->
      <div class="chart-card" v-show="selectedReport === 'velocity'">
        <div class="chart-header">
          <h3>🚀 Velocity Chart</h3>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-color planned"></span>
              Planned
            </span>
            <span class="legend-item">
              <span class="legend-color completed"></span>
              Completed
            </span>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="velocity-canvas" width="600" height="400"></canvas>
        </div>
      </div>

      <!-- Issue Breakdown -->
      <div class="chart-card breakdown-card" v-show="selectedReport === 'cumulative'">
        <h3>📊 Issue Breakdown</h3>
        <div class="breakdown-grid">
          <div class="breakdown-section">
            <h4>By Status</h4>
            <div class="breakdown-list">
              <div v-for="item in issueBreakdown.byStatus" :key="item.status" class="breakdown-item">
                <span class="breakdown-color" :style="{ backgroundColor: item.color }"></span>
                <span class="breakdown-label">{{ item.status }}</span>
                <span class="breakdown-count">{{ item.count }}</span>
              </div>
            </div>
          </div>
          
          <div class="breakdown-section">
            <h4>By Type</h4>
            <div class="breakdown-list">
              <div v-for="item in issueBreakdown.byType" :key="item.type" class="breakdown-item">
                <span class="breakdown-color" :style="{ backgroundColor: item.color }"></span>
                <span class="breakdown-label">{{ item.type }}</span>
                <span class="breakdown-count">{{ item.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Team Performance -->
      <div class="chart-card team-card" v-show="selectedReport === 'time-tracking'">
        <h3>⏱️ Team Performance</h3>
        <div class="team-performance">
          <div class="performance-header">
            <span>Team Member</span>
            <span>Completed</span>
            <span>Assigned</span>
            <span>Efficiency</span>
          </div>
          <div v-for="member in teamPerformance" :key="member.member" class="performance-row">
            <span class="member-name">{{ member.member }}</span>
            <span class="performance-stat completed">{{ member.completed }}</span>
            <span class="performance-stat assigned">{{ member.assigned }}</span>
            <div class="efficiency-container">
              <div class="efficiency-bar">
                <div class="efficiency-fill" :style="{ width: member.efficiency + '%' }"></div>
              </div>
              <span class="efficiency-text">{{ member.efficiency }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="quick-stats">
      <div class="stat-card">
        <div class="stat-icon">🎯</div>
        <div class="stat-info">
          <div class="stat-number">{{ Array.isArray(issueBreakdown.byStatus) ? issueBreakdown.byStatus.reduce((sum, item) => sum + item.count, 0) : 0 }}</div>
          <div class="stat-label">Total Issues</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-number">{{ Array.isArray(issueBreakdown.byStatus) ? (issueBreakdown.byStatus.find(item => item.status === 'Done')?.count || 0) : 0 }}</div>
          <div class="stat-label">Completed</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🔥</div>
        <div class="stat-info">
          <div class="stat-number"> {{ Array.isArray(issueBreakdown.byType) ? (issueBreakdown.byType.find(item => item.type === 'Bug')?.count || 0) : 0 }}</div>
          <div class="stat-label">Bugs</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-info">
          <div class="stat-number">{{ Array.isArray(sprintInfo) ? averageVelocity : 0 }}</div>
          <div class="stat-label">Avg Velocity</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

#burndown-canvas {
  width: 100%;
  height: 100%;
}

.reports-container {
  max-width: 1400px;
  margin: 0 auto;
  padding-bottom: 2rem;
}

.reports-header {
  margin-bottom: 2rem;
}

.reports-header h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 2rem;
}

.reports-description {
  color: #666;
  margin: 0 0 1.5rem 0;
  font-size: 1.1rem;
}

.report-controls {
  display: flex;
  gap: 2rem;
  align-items: end;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.control-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  min-width: 180px;
  font-size: 0.9rem;
  color: #222;
}

.control-select:focus {
  outline: none;
  border-color: #0066cc;
}

.sprint-overview {
  margin-bottom: 2rem;
}

.overview-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.overview-card h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #0066cc;
}

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

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-header h3 {
  margin: 0;
  color: #333;
}

.chart-legend {
  display: flex;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.ideal {
  background: #6c757d;
}

.legend-color.actual {
  background: #007bff;
}

.legend-color.planned {
  background: #e9ecef;
}

.legend-color.completed {
  background: #28a745;
}

.chart-container {
  width: 100%;
  height: 400px;
  position: relative;
}

.chart-container canvas {
  width: 100% !important;
  height: 100% !important;
  border-radius: 4px;
}

.breakdown-card {
  grid-column: span 1;
}

.breakdown-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.breakdown-section h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.breakdown-color {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  flex-shrink: 0;
}

.breakdown-label {
  flex: 1;
  font-weight: 500;
}

.breakdown-count {
  font-weight: bold;
  color: #0066cc;
  background: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  min-width: 30px;
  text-align: center;
}

.team-card {
  grid-column: span 1;
}

.team-performance {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.performance-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 2fr;
  gap: 1rem;
  font-weight: bold;
  color: #333;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.performance-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 2fr;
  gap: 1rem;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 4px;
}

.member-name {
  font-weight: 500;
  color: #333;
}

.performance-stat {
  text-align: center;
  font-weight: bold;
}

.performance-stat.completed {
  color: #28a745;
}

.performance-stat.assigned {
  color: #0066cc;
}

.efficiency-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.efficiency-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.efficiency-fill {
  height: 100%;
  background: linear-gradient(to right, #dc3545, #ffc107, #28a745);
  transition: width 0.3s ease;
}

.efficiency-text {
  font-size: 0.9rem;
  font-weight: bold;
  color: #333;
  min-width: 35px;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
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

.stat-card .stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #0066cc;
  margin: 0;
}

.stat-card .stat-label {
  font-size: 0.9rem;
  color: #666;
  margin: 0;
}

#velocity-canvas {
  width: 100%;
  height: 400px;
  border: 1px solid #ddd; /* Optional: for debugging */
}

@media (max-width: 1200px) {
  .breakdown-grid {
    grid-template-columns: 1fr;
  }
  
  .performance-header,
  .performance-row {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .performance-header {
    display: none;
  }
  
  .performance-row {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
}

@media (max-width: 768px) {
  .report-controls {
    flex-direction: column;
    gap: 1rem;
  }
  
  .overview-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .quick-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (prefers-color-scheme: dark) {
  .reports-container,
  .reports-header,
  .overview-card,
  .chart-card,
  .breakdown-card,
  .team-card,
  .stat-card {
    background: #181a1b !important;
    color: #f3f3f3 !important;
    border-color: #333 !important;
  }

  .reports-header h1,
  .reports-description,
  .overview-card h3,
  .chart-header h3,
  .breakdown-section h4,
  .stat-label,
  .stat-value,
  .member-name,
  .performance-stat,
  .efficiency-text,
  .stat-card .stat-number,
  .stat-card .stat-label {
    color: #f3f3f3 !important;
  }

  .control-group label {
    color: #f3f3f3 !important;
  }

  .control-select {
    background: #232526 !important;
    color: #f3f3f3 !important;
    border-color: #444 !important;
  }

  .control-select:focus {
    border-color: #4ea1ff !important;
  }

  .stat-value {
    color: #4ea1ff !important;
  }

  .progress-bar {
    background: #232526 !important;
  }

  .progress-fill {
    background: #4ea1ff !important;
  }

  .progress-text {
    color: #aaa !important;
  }

  .breakdown-item {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }

  .breakdown-count {
    background: #232526 !important;
    color: #4ea1ff !important;
    border: 1px solid #444 !important;
  }

  .performance-header {
    background: #232526 !important;
    color: #f3f3f3 !important;
  }

  .performance-row {
    background: #232526 !important;
    border-color: #444 !important;
    color: #f3f3f3 !important;
  }

  .performance-stat.completed {
    color: #4ea1ff !important;
  }

  .performance-stat.assigned {
    color: #4ea1ff !important;
  }

  .efficiency-bar {
    background: #232526 !important;
  }

  .stat-icon {
    background: #232526 !important;
  }

  .stat-card .stat-number {
    color: #4ea1ff !important;
  }

  .stat-card .stat-label {
    color: #aaa !important;
  }

  #burndown-canvas,
  #velocity-canvas {
    filter: invert(0.9) hue-rotate(180deg);
  }
}</style>