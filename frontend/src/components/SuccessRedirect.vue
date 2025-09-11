<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
onMounted(() => {
  router.replace('/home')
})
</script>
<template>
  <div>Redirecting...</div>
</template>