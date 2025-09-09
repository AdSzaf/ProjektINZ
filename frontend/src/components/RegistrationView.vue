<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const organization = ref('') // org id or invite code

// Form fields
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const role = ref('')
const password = ref('')
const confirmPassword = ref('')

// Validation states
const isPasswordMatch = ref(true)
const isEmailValid = ref(true)
const isPasswordValid = ref(false)

// Password validation criteria
const hasMinLength = ref(false)
const hasUppercase = ref(false)
const hasLowercase = ref(false)
const hasDigit = ref(false)

// Role options
const roles = [
  { value: 'developer', label: 'Developer' },
  { value: 'designer', label: 'Designer' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'tester', label: 'Tester' },
  { value: 'product_owner', label: 'Product Owner' },
  { value: 'scrum_master', label: 'Scrum Master' }
]
// Email validation (basic)
const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  isEmailValid.value = emailRegex.test(email.value)
}

watch(email, validateEmail)

// Password validation
const validatePassword = () => {
  hasMinLength.value = password.value.length >= 8
  hasUppercase.value = /[A-Z]/.test(password.value)
  hasLowercase.value = /[a-z]/.test(password.value)
  hasDigit.value = /\d/.test(password.value)

  isPasswordValid.value = hasMinLength.value && hasUppercase.value && hasLowercase.value && hasDigit.value
}

// Check password match
const checkPasswordMatch = () => {
  isPasswordMatch.value = password.value === confirmPassword.value
}

watch(password, () => {
  validatePassword()
  checkPasswordMatch()
})
watch(confirmPassword, checkPasswordMatch)

// Form submission validation
const canSubmit = computed(() => {
  return (
    firstName.value.trim() !== '' &&
    lastName.value.trim() !== '' &&
    email.value.trim() !== '' &&
    isEmailValid.value &&
    role.value !== '' &&
    isPasswordValid.value &&
    isPasswordMatch.value &&
    confirmPassword.value !== ''
  )
})

// Handle registration
const handleRegister = async () => {
  if (!canSubmit.value) return

  const userData = {
    first_name: firstName.value.trim(),
    last_name: lastName.value.trim(),
    email: email.value.trim(),
    role: role.value,
    password: password.value,
    organization: organization.value.trim() || null,
    // Optionally: organization_name: orgName.value
  }

  try {
    await axios.post('/api/register/', userData)
    console.log('Data sent:', userData)
    alert('Registration successful!')
    router.push('/login')
  } catch (error) {
    alert('Registration failed: ' + (error.response?.data?.detail || error.message))
  }
}

// Navigate to login
const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="register-view">
    <div class="register-container">
      <h2>Create Account</h2>
      
      <form @submit.prevent="handleRegister">
        <!-- First Name -->
        <div class="form-group">
          <label for="firstName">First Name</label>
          <input
            type="text"
            id="firstName"
            v-model="firstName"
            required
            placeholder="Enter your first name"
          />
        </div>

        <!-- Last Name -->
        <div class="form-group">
          <label for="lastName">Last Name</label>
          <input
            type="text"
            id="lastName"
            v-model="lastName"
            required
            placeholder="Enter your last name"
          />
        </div>

        <!-- Email -->
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            type="email"
            id="email"
            v-model="email"
            required
            placeholder="Enter your email address"
            :class="{ 'error': email && !isEmailValid }"
          />
          <span v-if="email && !isEmailValid" class="error-text">Invalid email format</span>
        </div>

        <!-- Organization (optional) -->
        <div class="form-group">
          <label for="organization">Organization (optional)</label>
          <input
            type="text"
            id="organization"
            v-model="organization"
            placeholder="Enter organization name or invite code"
          />
        </div>

        <!-- Role Selection -->
        <div class="form-group">
          <label for="role">Role in Project</label>
          <select
            id="role"
            v-model="role"
            required
          >
            <option value="" disabled>Select your role</option>
            <option
              v-for="roleOption in roles"
              :key="roleOption.value"
              :value="roleOption.value"
            >
              {{ roleOption.label }}
            </option>
          </select>
        </div>

        <!-- Password -->
        <div class="form-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            required
            placeholder="Create a password"
          />
        </div>

        <!-- Confirm Password -->
        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            v-model="confirmPassword"
            required
            placeholder="Confirm your password"
            :class="{ 'error': confirmPassword && !isPasswordMatch }"
          />
          <span v-if="confirmPassword && !isPasswordMatch" class="error-text">Passwords don't match</span>
        </div>

        <!-- Password Requirements -->
        <div v-if="password" class="password-requirements">
          <p class="requirements-title">Password must have:</p>
          <ul>
            <li :class="{ 'valid': hasMinLength }">
              At least 8 characters
              <span v-if="hasMinLength" class="check">✓</span>
            </li>
            <li :class="{ 'valid': hasUppercase }">
              One uppercase letter
              <span v-if="hasUppercase" class="check">✓</span>
            </li>
            <li :class="{ 'valid': hasLowercase }">
              One lowercase letter
              <span v-if="hasLowercase" class="check">✓</span>
            </li>
            <li :class="{ 'valid': hasDigit }">
              One number
              <span v-if="hasDigit" class="check">✓</span>
            </li>
          </ul>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          class="register-btn"
          :disabled="!canSubmit"
        >
          Register
        </button>
      </form>

      <!-- Login Link -->
      <div class="login-link">
        <p>Already have an account? <a @click="goToLogin" href="#">Go to login</a></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #27ae60;
  width: 100%;
}

.register-container {
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

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 500;
}

input,
select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

input:focus,
select:focus {
  outline: none;
  border-color: #0066cc;
}

input.error {
  border-color: #e74c3c;
}

select {
  cursor: pointer;
}

.password-requirements {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #0066cc;
}

.requirements-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.password-requirements ul {
  margin: 0;
  padding-left: 1rem;
  list-style: none;
}

.password-requirements li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.9rem;
  color: #666;
  transition: color 0.2s;
}

.password-requirements li.valid {
  color: #27ae60;
}

.check {
  color: #27ae60;
  font-weight: bold;
}

.register-btn {
  width: 100%;
  padding: 0.75rem;
  background-color: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.register-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.register-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
}

.login-link p {
  margin: 0;
  color: #666;
}

.login-link a {
  color: #0066cc;
  cursor: pointer;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}

.error-text {
  color: #e74c3c;
  font-size: 0.85rem;
  font-weight: 500;
}
</style>