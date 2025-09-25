<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const status = ref('Loading...')

onMounted(async () => {
  const { uid, token } = route.params
  try {
    const res = await axios.get(`/api/activate/${uid}/${token}/`)
    status.value = res.data.message || 'Account activated successfully!'
    // Opcjonalnie przekieruj po chwili do logowania
    setTimeout(() => router.push('/login'), 3000)
  } catch (err) {
    status.value = err.response?.data?.error || 'Invalid or expired activation link.'
  }
})
</script>

<template>
  <div class="activate-view">
    <h2>{{ status }}</h2>
    <p v-if="status.includes('successfully')">Redirecting to login...</p>
  </div>
</template>
<style scoped>

</style>
