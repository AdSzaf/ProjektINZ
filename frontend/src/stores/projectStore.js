// stores/projectStore.js
import { defineStore } from 'pinia'
import axios from 'axios'

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    selectedProject: null,
  }),
  actions: {
    async fetchProjects() {
      const token = localStorage.getItem('token')
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
      const res = await axios.get('/api/projects/')
      // Remove duplicates by id
      const unique = []
      const seen = new Set()
      for (const p of res.data) {
        if (!seen.has(p.id)) {
          unique.push(p)
          seen.add(p.id)
        }
      }
      this.projects = unique
      // Set selected project if not set
      if (!this.selectedProject && this.projects.length > 0) {
        this.setProject(this.projects[0])
      }
      // Restore last selected project if available
      const lastId = localStorage.getItem('selectedProjectId')
      if (lastId) {
        const found = this.projects.find(p => p.id === lastId)
        if (found) this.setProject(found)
      }
    },
    setProject(project) {
      this.selectedProject = project
      localStorage.setItem('selectedProjectId', project.id)
    },
    loadFromLocal(projects) {
      const lastId = localStorage.getItem('selectedProjectId')
      if (lastId) {
        const found = projects.find(p => p.id === lastId)
        if (found) this.selectedProject = found
      }
    }
  }
})