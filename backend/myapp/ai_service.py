import os
import httpx

class MistralAssistant:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = "mistral-small-latest"  # or mistral-medium-latest, mistral-tiny, etc.

    def get_ai_response(self, user_message: str, context_data: dict = None) -> str:
        if not self.api_key:
            return "Mistral API key not configured."
        context = ""
        if context_data:
            total = context_data.get('total_tasks', 0)
            completed = context_data.get('completed_tasks', 0)
            in_progress = context_data.get('in_progress_tasks', 0)
            context = f"Project context: {total} total tasks, {completed} completed, {in_progress} in progress. "
        prompt = f"{context}User question: {user_message}\nPlease provide helpful, concise project management advice. Keep your response under 150 words."
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert project assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.7,
            }
            response = httpx.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Mistral error: {e}"

    def analyze_tasks(self, tasks: list, user_message: str) -> str:
        if not tasks:
            return "No tasks to analyze."
        task_list = "\n".join([
            f"- {task.get('title', 'Task')} (Status: {task.get('status', 'Unknown')}, Priority: {task.get('priority', 'Normal')}, Assignee: {task.get('assignee', 'Unassigned')}, Story Points: {task.get('story_points', '-')})"
            for task in tasks[:10]
        ])
        prompt = f"""You are an expert project assistant. Here is a list of tasks in my project:
{task_list}

Based ONLY on the above tasks, answer the user's question below.
If the user asks which task to do next, pick one or two tasks from the list that are NOT marked as 'done' and explain why, using their status and priority.
Never suggest tasks with status 'done'.
Do NOT give generic advice.
If you can't answer using the list, say "I need more information."

User: {user_message}
Assistant:"""
        return self.get_ai_response(prompt)

ai_service = MistralAssistant()