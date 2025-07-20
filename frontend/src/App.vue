<script setup>
import HelloWorld from './components/HelloWorld.vue'
import { ref } from 'vue';
import Login from './components/Login.vue';
import Registration from './components/Registration.vue';
</script>

<template>
  <Registration />
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
body {
  margin: 0;
  padding: 0;
  width: 100%;
  background-color: #f5f5f5;
}

.app-layout {
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: center;
  justify-content: center;

  min-height: 100vh;
  background-color: white; /* Ensure white background */
}
</style>
