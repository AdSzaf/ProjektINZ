<script setup>
import { ref, computed, onMounted } from 'vue'

// Report data
const selectedTimeframe = ref('current-sprint')
const selectedReport = ref('burndown')

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

// Sprint data
const sprintInfo = ref({
  name: 'Sprint 23',
  startDate: '2025-07-14',
  endDate: '2025-07-27',
  totalStoryPoints: 45,
  completedStoryPoints: 29,
  remainingStoryPoints: 16,
  totalDays: 14,
  remainingDays: 1
})

// Burndown chart data (story points remaining per day)
const burndownData = ref([
  { day: 0, ideal: 45, actual: 45, date: '2025-07-14' },
  { day: 1, ideal: 42, actual: 45, date: '2025-07-15' },
  { day: 2, ideal: 39, actual: 43, date: '2025-07-16' },
  { day: 3, ideal: 36, actual: 40, date: '2025-07-17' },
  { day: 4, ideal: 33, actual: 38, date: '2025-07-18' },
  { day: 5, ideal: 30, actual: 35, date: '2025-07-19' },
  { day: 6, ideal: 27, actual: 35, date: '2025-07-20' },
  { day: 7, ideal: 24, actual: 32, date: '2025-07-21' },
  { day: 8, ideal: 21, actual: 28, date: '2025-07-22' },
  { day: 9, ideal: 18, actual: 25, date: '2025-07-23' },
  { day: 10, ideal: 15, actual: 22, date: '2025-07-24' },
  { day: 11, ideal: 12, actual: 19, date: '2025-07-25' },
  { day: 12, ideal: 9, actual: 16, date: '2025-07-26' },
  { day: 13, ideal: 6, actual: 16, date: '2025-07-27' }
])

// Velocity data (last 6 sprints)
const velocityData = ref([
  { sprint: 'Sprint 18', planned: 38, completed: 35 },
  { sprint: 'Sprint 19', planned: 42, completed: 40 },
  { sprint: 'Sprint 20', planned: 45, completed: 41 },
  { sprint: 'Sprint 21', planned: 40, completed: 43 },
  { sprint: 'Sprint 22', planned: 47, completed: 44 },
  { sprint: 'Sprint 23', planned: 45, completed: 29 }
])

// Issue breakdown data
const issueBreakdown = ref({
  byStatus: [
    { status: 'To Do', count: 8, color: '#6c757d' },
    { status: 'In Progress', count: 5, color: '#007bff' },
    { status: 'Code Review', count: 3, color: '#ffc107' },
    { status: 'Testing', count: 2, color: '#fd7e14' },
    { status: 'Done', count: 18, color: '#28a745' }
  ],
  byType: [
    { type: 'Story', count: 20, color: '#28a745' },
    { type: 'Bug', count: 12, color: '#dc3545' },
    { type: 'Task', count: 8, color: '#007bff' },
    { type: 'Epic', count: 2, color: '#6f42c1' }
  ]
})

// Team performance data
const teamPerformance = ref([
  { member: 'Alice Johnson', completed: 12, assigned: 15, efficiency: 80 },
  { member: 'Bob Smith', completed: 10, assigned: 12, efficiency: 83 },
  { member: 'Charlie Brown', completed: 8, assigned: 10, efficiency: 80 },
  { member: 'Diana Wilson', completed: 6, assigned: 8, efficiency: 75 }
])

// Computed properties
const sprintProgressPercentage = computed(() => {
  return Math.round((sprintInfo.value.completedStoryPoints / sprintInfo.value.totalStoryPoints) * 100)
})

const averageVelocity = computed(() => {
  const total = velocityData.value.reduce((sum, sprint) => sum + sprint.completed, 0)
  return Math.round(total / velocityData.value.length)
})

const maxBurndownValue = computed(() => {
  return Math.max(...burndownData.value.map(d => Math.max(d.ideal, d.actual)))
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
  const width = canvas.width
  const height = canvas.height
  
  ctx.clearRect(0, 0, width, height)
  
  const padding = 40
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding
  const barWidth = chartWidth / velocityData.value.length * 0.8
  const barSpacing = chartWidth / velocityData.value.length * 0.2
  
  const maxValue = Math.max(...velocityData.value.map(d => Math.max(d.planned, d.completed)))
  const yScale = chartHeight / maxValue
  
  // Draw bars
  velocityData.value.forEach((sprint, index) => {
    const x = padding + (chartWidth / velocityData.value.length) * index + barSpacing / 2
    
    // Planned bar (background)
    const plannedHeight = sprint.planned * yScale
    ctx.fillStyle = '#e9ecef'
    ctx.fillRect(x, height - padding - plannedHeight, barWidth, plannedHeight)
    
    // Completed bar (foreground)
    const completedHeight = sprint.completed * yScale
    ctx.fillStyle = index === velocityData.value.length - 1 ? '#007bff' : '#28a745'
    ctx.fillRect(x, height - padding - completedHeight, barWidth, completedHeight)
    
    // Labels
    ctx.fillStyle = '#333'
    ctx.font = '10px Arial'
    ctx.textAlign = 'center'
    ctx.save()
    ctx.translate(x + barWidth / 2, height - 10)
    ctx.rotate(-Math.PI / 4)
    ctx.fillText(sprint.sprint.replace('Sprint ', 'S'), 0, 0)
    ctx.restore()
  })
}

onMounted(() => {
  // Set canvas sizes
  const burndownCanvas = document.getElementById('burndown-canvas')
  const velocityCanvas = document.getElementById('velocity-canvas')
  
  if (burndownCanvas) {
    burndownCanvas.width = burndownCanvas.offsetWidth * 2
    burndownCanvas.height = burndownCanvas.offsetHeight * 2
    burndownCanvas.style.width = burndownCanvas.offsetWidth / 2 + 'px'
    burndownCanvas.style.height = burndownCanvas.offsetHeight / 2 + 'px'
    drawBurndownChart()
  }
  
  if (velocityCanvas) {
    velocityCanvas.width = velocityCanvas.offsetWidth * 2
    velocityCanvas.height = velocityCanvas.offsetHeight * 2
    velocityCanvas.style.width = velocityCanvas.offsetWidth / 2 + 'px'
    velocityCanvas.style.height = velocityCanvas.offsetHeight / 2 + 'px'
    drawVelocityChart()
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
    <div class="sprint-overview">
      <div class="overview-card">
        <h3>{{ sprintInfo.name }} Overview</h3>
        <div class="overview-stats">
          <div class="stat">
            <span class="stat-label">Progress</span>
            <span class="stat-value">{{ sprintProgressPercentage }}%</span>
          </div>
          <div class="stat">
            <span class="stat-label">Completed</span>
            <span class="stat-value">{{ sprintInfo.completedStoryPoints }}/{{ sprintInfo.totalStoryPoints }} SP</span>
          </div>
          <div class="stat">
            <span class="stat-label">Days Left</span>
            <span class="stat-value">{{ sprintInfo.remainingDays }}</span>
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
          <div class="progress-text">{{ sprintInfo.completedStoryPoints }} of {{ sprintInfo.totalStoryPoints }} story points completed</div>
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
          <canvas id="velocity-canvas" width="800" height="400"></canvas>
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
          <div class="stat-number">{{ issueBreakdown.byStatus.reduce((sum, item) => sum + item.count, 0) }}</div>
          <div class="stat-label">Total Issues</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-number">{{ issueBreakdown.byStatus.find(item => item.status === 'Done')?.count || 0 }}</div>
          <div class="stat-label">Completed</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🔥</div>
        <div class="stat-info">
          <div class="stat-number">{{ issueBreakdown.byType.find(item => item.type === 'Bug')?.count || 0 }}</div>
          <div class="stat-label">Bugs</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-info">
          <div class="stat-number">{{ averageVelocity }}</div>
          <div class="stat-label">Avg Velocity</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-container {
  max-width: 1400px;
  margin: 0 auto;
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
  width: 100%;
  height: 100%;
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
</style>