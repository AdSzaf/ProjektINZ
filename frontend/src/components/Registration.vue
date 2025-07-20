<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  role: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false
})

const errors = reactive({})
const loading = ref(false)
const showPassword = ref(false)

const passwordStrength = computed(() => {
  const password = form.password
  if (!password) return 0
  let strength = 0
  if (password.length >= 8) strength++
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++
  if (/\d/.test(password) && /[^A-Za-z\d]/.test(password)) strength++
  return strength
})

const passwordStrengthText = computed(() => {
  switch (passwordStrength.value) {
    case 0: return 'Password too weak'
    case 1: return 'Weak password'
    case 2: return 'Good password'
    case 3: return 'Strong password'
    default: return ''
  }
})

const passwordStrengthColor = computed(() => {
  switch (passwordStrength.value) {
    case 1: return 'bg-red-500'
    case 2: return 'bg-yellow-500'
    case 3: return 'bg-green-500'
    default: return 'bg-gray-200'
  }
})

const validateForm = () => {
  Object.keys(errors).forEach(key => delete errors[key])
  if (!form.firstName.trim()) errors.firstName = 'First name is required'
  if (!form.lastName.trim()) errors.lastName = 'Last name is required'
  if (!form.email) errors.email = 'Email is required'
  else if (!/\S+@\S+\.\S+/.test(form.email)) errors.email = 'Please enter a valid email'
  if (!form.role) errors.role = 'Please select your role'
  if (!form.password) errors.password = 'Password is required'
  else if (form.password.length < 8) errors.password = 'Password must be at least 8 characters'
  if (!form.confirmPassword) errors.confirmPassword = 'Please confirm your password'
  else if (form.password !== form.confirmPassword) errors.confirmPassword = 'Passwords do not match'
  if (!form.acceptTerms) errors.acceptTerms = 'You must agree to the terms and privacy policy'
}

const handleRegister = async () => {
  loading.value = true
  try {
    validateForm()
    if (Object.keys(errors).length > 0) {
      loading.value = false
      return
    }
    // TODO: Replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    router.push('/login')
  } catch (error) {
    errors.general = 'Failed to create account. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md space-y-8">
      <div class="text-center">
        <h2 class="mt-6 text-3xl font-bold text-gray-900">Create your account</h2>
        <p class="mt-2 text-sm text-gray-600">Join AgilePro workspace</p>
      </div>
      <div class="bg-white py-8 px-6 shadow-lg rounded-lg border border-gray-200">
        <form @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label for="firstName" class="block text-sm font-medium text-gray-700 mb-1">First name</label>
            <input id="firstName" v-model="form.firstName" type="text" required
              class="w-full px-4 py-3 text-base border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': errors.firstName }"
              placeholder="John" />
            <p v-if="errors.firstName" class="mt-1 text-sm text-red-600">{{ errors.firstName }}</p>
          </div>
          <div>
            <label for="lastName" class="block text-sm font-medium text-gray-700 mb-1">Last name</label>
            <input id="lastName" v-model="form.lastName" type="text" required
              class="w-full px-4 py-3 text-base border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': errors.lastName }"
              placeholder="Doe" />
            <p v-if="errors.lastName" class="mt-1 text-sm text-red-600">{{ errors.lastName }}</p>
          </div>
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email address</label>
            <input id="email" v-model="form.email" type="email" required
              class="w-full px-4 py-3 text-base border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': errors.email }"
              placeholder="john.doe@company.com" />
            <p v-if="errors.email" class="mt-1 text-sm text-red-600">{{ errors.email }}</p>
          </div>
          <div>
            <label for="role" class="block text-sm font-medium text-gray-700 mb-1">Your role</label>
            <select id="role" v-model="form.role"
              class="w-full px-4 py-3 text-base border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': errors.role }">
              <option value="">Select your role</option>
              <option value="project_manager">Project Manager</option>
              <option value="developer">Developer</option>
              <option value="designer">Designer</option>
              <option value="tester">Tester</option>
              <option value="stakeholder">Stakeholder</option>
            </select>
            <p v-if="errors.role" class="mt-1 text-sm text-red-600">{{ errors.role }}</p>
          </div>
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div class="relative">
              <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'" required
                class="w-full px-4 py-3 pr-10 text-base border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': errors.password }"
                placeholder="Create a strong password" />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600">
                <span class="text-sm">{{ showPassword ? 'Hide' : 'Show' }}</span>
              </button>
            </div>
            <p v-if="errors.password" class="mt-1 text-sm text-red-600">{{ errors.password }}</p>
            <div v-if="form.password" class="mt-2">
              <div class="flex space-x-1">
                <div class="h-2 flex-1 rounded" :class="passwordStrength >= 1 ? passwordStrengthColor : 'bg-gray-200'"></div>
                <div class="h-2 flex-1 rounded" :class="passwordStrength >= 2 ? passwordStrengthColor : 'bg-gray-200'"></div>
                <div class="h-2 flex-1 rounded" :class="passwordStrength >= 3 ? passwordStrengthColor : 'bg-gray-200'"></div>
              </div>
              <p class="mt-1 text-xs text-gray-500">{{ passwordStrengthText }}</p>
            </div>
          </div>
          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
            <input id="confirmPassword" v-model="form.confirmPassword" type="password" required
              class="w-full px-4 py-3 text-base border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': errors.confirmPassword }"
              placeholder="Confirm your password" />
            <p v-if="errors.confirmPassword" class="mt-1 text-sm text-red-600">{{ errors.confirmPassword }}</p>
          </div>
          <div class="flex items-start">
            <input id="terms" v-model="form.acceptTerms" type="checkbox"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1" />
            <div class="ml-3 text-sm">
              <label for="terms" class="text-gray-700">
                I agree to the
                <a href="#" class="font-medium text-blue-600 hover:text-blue-500">Terms of Service</a>
                and
                <a href="#" class="font-medium text-blue-600 hover:text-blue-500">Privacy Policy</a>
              </label>
            </div>
          </div>
          <p v-if="errors.acceptTerms" class="text-sm text-red-600">{{ errors.acceptTerms }}</p>
          <div v-if="errors.general" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ errors.general }}</p>
          </div>
          <div>
            <button type="submit" :disabled="loading || !form.acceptTerms"
              class="group relative w-full flex justify-center py-3 px-4 text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200">
              <span v-if="loading" class="mr-2">
                <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </span>
              {{ loading ? 'Creating account...' : 'Create account' }}
            </button>
          </div>
        </form>
        <div class="mt-6">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-300" />
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-white text-gray-500">Already have an account?</span>
            </div>
          </div>
          <div class="mt-6">
            <router-link to="/login"
              class="w-full flex justify-center py-3 px-4 text-base font-medium rounded-md text-blue-600 bg-white border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200">
              Sign in instead
            </router-link>
          </div>
        </div>
      </div>
      <p class="text-center text-xs text-gray-500">© 2025 AgilePro. All rights reserved.</p>
    </div>
  </div>
</template>

<style scoped>
input:focus, select:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
button[type="submit"] {
  min-height: 48px;
}
input[type="checkbox"] {
  flex-shrink: 0;
}
</style>