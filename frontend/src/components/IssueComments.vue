<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  issueId: { type: [String, Number], required: true },
  show: { type: Boolean, default: true }
})

const comments = ref([])
const newComment = ref('')
const isLoading = ref(false)
const error = ref('')

const fetchComments = async () => {
  if (!props.issueId) return
  isLoading.value = true
  error.value = ''
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    const res = await axios.get(`/api/issues/${props.issueId}/comments/`)
    comments.value = res.data
  } catch (e) {
    error.value = 'Failed to load comments.'
  } finally {
    isLoading.value = false
  }
}

const postComment = async () => {
  if (!newComment.value.trim()) return
  isLoading.value = true
  error.value = ''
  try {
    const token = localStorage.getItem('token')
    axios.defaults.headers.common['Authorization'] = `Token ${token}`
    await axios.post(`/api/issues/${props.issueId}/comments/`, {
      content: newComment.value
    })
    newComment.value = ''
    await fetchComments()
  } catch (e) {
    error.value = 'Failed to post comment.'
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchComments)
watch(() => props.issueId, fetchComments)
</script>

<template>
  <div v-if="show" class="comments-section">
    <h4>Comments</h4>
    <div v-if="isLoading" class="comments-loading">Loading...</div>
    <div v-if="error" class="comments-error">{{ error }}</div>
    <div v-if="comments.length === 0 && !isLoading" class="comments-empty">No comments yet.</div>
    <div v-for="comment in comments" :key="comment.id" class="comment-item">
      <div class="comment-meta">
        <span class="comment-author">{{ comment.author_name || 'User' }}</span>
        <span class="comment-date">{{ comment.created_at?.slice(0, 16).replace('T', ' ') }}</span>
      </div>
      <div class="comment-content">{{ comment.content }}</div>
    </div>
    <div class="comment-form">
      <textarea v-model="newComment" placeholder="Add a comment..." rows="2"></textarea>
      <button @click="postComment" :disabled="isLoading || !newComment.trim()" class="comment-btn">Post</button>
    </div>
  </div>
</template>

<style scoped>
.comments-section {
  margin-top: 1.5rem;
  background: #f6f8fa;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e1e4e8;
}

.comments-section h4 {
  margin: 0 0 1rem 0;
  color: #24292e;
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.comments-loading, 
.comments-error, 
.comments-empty {
  color: #656d76;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  padding: 0.75rem;
  border-radius: 6px;
  background: white;
  border: 1px solid #e1e4e8;
}

.comments-error {
  color: #d73a49;
  background: #ffeef0;
  border-color: #fdaeb7;
}

.comment-item {
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e1e4e8;
  transition: border-color 0.15s ease;
}

.comment-item:hover {
  border-color: #d1d5da;
}

.comment-item:last-of-type {
  margin-bottom: 0;
}

.comment-meta {
  font-size: 0.875rem;
  color: #656d76;
  margin-bottom: 0.5rem;
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.comment-author {
  font-weight: 600;
  color: #24292e;
}

.comment-date {
  color: #656d76;
  font-size: 0.8125rem;
}

.comment-content {
  font-size: 0.875rem;
  color: #24292e;
  line-height: 1.6;
  word-wrap: break-word;
}

.comment-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e1e4e8;
}

.comment-form textarea {
  width: 100%;
  border-radius: 6px;
  border: 1px solid #d1d5da;
  padding: 0.75rem;
  font-size: 0.875rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  resize: vertical;
  min-height: 60px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

.comment-form textarea:focus {
  border-color: #0969da;
  outline: none;
  box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
}

.comment-btn {
  align-self: flex-end;
  background: #2ea043;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.875rem;
  transition: background-color 0.15s ease;
}

.comment-btn:hover:not(:disabled) {
  background: #2c974b;
}

.comment-btn:disabled {
  background: #94d3a2;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
  .comments-section {
    background: #0d1117 !important;
    border-color: #30363d !important;
  }

  .comments-section h4 {
    color: #f0f6fc !important;
  }

  .comments-loading, 
  .comments-empty {
    color: #8b949e !important;
    background: #161b22 !important;
    border-color: #30363d !important;
  }

  .comments-error {
    color: #ff7b72 !important;
    background: #2d1b20 !important;
    border-color: #6e2c2f !important;
  }

  .comment-item {
    background: #161b22 !important;
    border-color: #30363d !important;
  }

  .comment-item:hover {
    border-color: #484f58 !important;
  }

  .comment-meta {
    color: #8b949e !important;
  }

  .comment-author {
    color: #f0f6fc !important;
  }

  .comment-date {
    color: #8b949e !important;
  }

  .comment-content {
    color: #c9d1d9 !important;
  }

  .comment-form {
    background: #161b22 !important;
    border-color: #30363d !important;
  }

  .comment-form textarea {
    background: #0d1117 !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
  }

  .comment-form textarea:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.3) !important;
  }

  .comment-form textarea::placeholder {
    color: #8b949e !important;
  }

  .comment-btn {
    background: #238636 !important;
  }

  .comment-btn:hover:not(:disabled) {
    background: #2ea043 !important;
  }

  .comment-btn:disabled {
    background: #1b4721 !important;
    opacity: 0.6 !important;
  }
}
</style>