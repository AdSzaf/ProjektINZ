# ai_service.py
import requests
import json
import logging

logger = logging.getLogger(__name__)

class LocalAIService:
    def __init__(self):
        self.ollama_url = "http://ollama:11434"  # or "http://ollama:11434" if using Docker or http://localhost:11434 if running locally
        self.model = "llama2:7b-chat"
    
    def is_available(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_ai_response(self, user_message: str, context_data: dict = None) -> str:
        """Get AI response for any question"""
        if not self.is_available():
            return "Local AI is starting up. Please try again in a moment."
        
        # Build context
        context = ""
        if context_data:
            total = context_data.get('total_tasks', 0)
            completed = context_data.get('completed_tasks', 0)
            in_progress = context_data.get('in_progress_tasks', 0)
            context = f"Project context: {total} total tasks, {completed} completed, {in_progress} in progress. "
        
        # Create prompt
        prompt = f"""{context}User question: {user_message}

Please provide helpful, concise project management advice. Keep your response under 150 words."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 150
                    }
                },
                timeout=1200  # Increase timeout for first load
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                return "I'm having trouble right now. Please try again."
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return "I'm currently processing your request. Please try again in a moment."
    
    def analyze_tasks(self, tasks: list, user_message: str) -> str:
        """Analyze task priority"""
        if not tasks:
            return "No tasks to analyze."

        task_list = "\n".join([
            f"- {task.get('title', 'Task')} (Status: {task.get('status', 'Unknown')}, Priority: {task.get('priority', 'Normal')}, Assignee: {task.get('assignee', 'Unassigned')}, Story Points: {task.get('story_points', '-')})"
            for task in tasks[:10]
        ])

        prompt = f"""You are an expert project assistant. Here is a list of tasks in my project:
    {task_list}

    Based ONLY on the above tasks, answer the user's question below. 
    If the user asks which task to do next, pick one or two tasks from the list and explain why, using their status and priority. 
    Do NOT give generic advice. 
    If you can't answer using the list, say "I need more information."

    User: {user_message}
    Assistant:"""
        return self.get_ai_response(prompt)

# Initialize the service
ai_service = LocalAIService()