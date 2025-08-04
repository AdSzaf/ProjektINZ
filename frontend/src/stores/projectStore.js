// stores/projectStore.js
import { defineStore } from 'pinia'
export const useProjectStore = defineStore('project', {
  state: () => ({
    selectedProject: null,
  }),
  actions: {
    setProject(project) {
      console.log('Setting project in store:', project)
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