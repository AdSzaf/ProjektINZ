import os
import httpx
from .models import Sprint, Issue  # Import your models here

class MistralAssistant:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = "mistral-small-latest"  # or mistral-medium-latest, mistral-tiny, etc.

    def get_ai_response(self, prompt: str) -> str:
        if not self.api_key:
            return "Mistral API key not configured."
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

# Standalone function for context extraction
def get_ai_context_for_message(user_message, project):
    user_message = user_message.lower()
    context = {}

    if "sprint" in user_message or "velocity" in user_message:
        # Sprint/velocity context
        sprints = Sprint.objects.filter(project=project).order_by('-start_date')[:5]
        context['sprints'] = [
            {
                "name": s.name,
                "status": s.status,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
                "completed_issues": Issue.objects.filter(sprint=s, status__iexact='done').count(),
                "total_issues": Issue.objects.filter(sprint=s).count(),
            }
            for s in sprints
        ]
    elif "team" in user_message or "member" in user_message or "performance" in user_message:
        # Team performance context
        members = project.members.all()
        context['members'] = [
            {
                "name": f"{m.first_name} {m.last_name}",
                "completed_issues": Issue.objects.filter(project=project, assignee=m, status__iexact='done').count(),
                "assigned_issues": Issue.objects.filter(project=project, assignee=m).count(),
            }
            for m in members
        ]
    else:
        # Default: issues/tasks context
        issues = Issue.objects.filter(project=project).order_by('-priority')[:10]
        context['issues'] = [
            {
                "title": i.title,
                "status": i.status,
                "priority": i.priority,
                "assignee": i.assignee.first_name if i.assignee else None,
                "story_points": i.story_points,
            }
            for i in issues
        ]
    return context

ai_service = MistralAssistant()