<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Form fields
const email = ref('')
const password = ref('')

// Loading state
const isLoading = ref(false)

// Form validation
const canSubmit = computed(() => {
  return email.value.trim() !== '' && password.value.trim() !== ''
})

// Handle login
const handleLogin = async () => {
  if (!canSubmit.value || isLoading.value) return

  isLoading.value = true

  const loginData = {
    email: email.value.trim(),
    password: password.value
  }

  try {
    // Here you would make your API call
    // const response = await axios.post('/api/login', loginData)
    
    console.log('Login data:', loginData)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    alert('Login successful!')
    router.push('/dashboard') // or wherever you want to redirect after login
  } catch (error) {
    console.error('Login error:', error)
    alert('Login failed. Please check your credentials and try again.')
  } finally {
    isLoading.value = false
  }
}

// Navigate to registration
const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="login-view">
    <div class="login-container">
      <h2>Sign In</h2>
      
      <form @submit.prevent="handleLogin">
        <!-- Email -->
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            type="email"
            id="email"
            v-model="email"
            required
            placeholder="Enter your email address"
            :disabled="isLoading"
          />
        </div>

        <!-- Password -->
        <div class="form-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            required
            placeholder="Enter your password"
            :disabled="isLoading"
          />
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          class="login-btn"
          :disabled="!canSubmit || isLoading"
        >
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <!-- Register Link -->
      <div class="register-link">
        <p>Don't have an account? <a @click="goToRegister" href="#">Register here</a></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #27ae60;
  width: 100%;
}

.login-container {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 35%;
}

h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #333;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #0066cc;
}

input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.login-btn {
  width: 100%;
  padding: 0.75rem;
  background-color: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 1rem;
}

.login-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.login-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
}

.register-link p {
  margin: 0;
  color: #666;
}

.register-link a {
  color: #0066cc;
  cursor: pointer;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>