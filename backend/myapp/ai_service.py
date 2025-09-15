# ai_service.py
import os
import requests
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: int
    title: str
    description: str
    status: str
    priority: str
    assignee: str
    created_date: str
    sprint_id: int = None

class AIAssistantService:
    def __init__(self):
        self.hf_api_key = os.getenv("HF_API_KEY")
        # Using a better model for conversational AI
        self.model_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        self.headers = {"Authorization": f"Bearer {self.hf_api_key}"}
    
    def _call_huggingface_api(self, prompt: str, max_length: int = 200) -> str:
        """Call Hugging Face API with proper error handling"""
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": 0.7,
                "do_sample": True,
                "pad_token_id": 50256
            }
        }
        
        try:
            response = requests.post(
                self.model_url, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 503:
                # Model is loading, try again after a short wait
                import time
                time.sleep(2)
                response = requests.post(self.model_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
                return "I'm having trouble generating a response right now."
            else:
                return f"Sorry, I encountered an error (Status: {response.status_code})"
                
        except requests.exceptions.RequestException as e:
            return "I'm currently unavailable. Please try again later."
    
    def analyze_tasks_priority(self, tasks: List[Dict]) -> str:
        """Analyze tasks and suggest priority order"""
        if not tasks:
            return "No tasks provided to analyze."
        
        task_summary = []
        for task in tasks:
            task_summary.append(f"- {task.get('title', 'Untitled')}: {task.get('status', 'Unknown')} priority ({task.get('priority', 'Normal')})")
        
        prompt = f"""As a project manager, analyze these tasks and suggest the order of execution:

{chr(10).join(task_summary)}

Consider factors like dependencies, priority, and team capacity. Provide a brief recommendation:"""
        
        return self._call_huggingface_api(prompt, max_length=300)
    
    def suggest_sprint_planning(self, tasks: List[Dict], sprint_capacity: int = 10) -> str:
        """Suggest which tasks to include in upcoming sprint"""
        if not tasks:
            return "No tasks available for sprint planning."
        
        high_priority_tasks = [t for t in tasks if t.get('priority', '').lower() in ['high', 'urgent']]
        pending_tasks = [t for t in tasks if t.get('status', '').lower() in ['todo', 'open', 'new']]
        
        prompt = f"""Sprint Planning Recommendation:

Available tasks: {len(tasks)}
High priority tasks: {len(high_priority_tasks)}
Pending tasks: {len(pending_tasks)}
Sprint capacity: {sprint_capacity} tasks

Based on this information, suggest which types of tasks to prioritize for the next sprint and provide general planning advice."""
        
        return self._call_huggingface_api(prompt, max_length=250)
    
    def get_task_recommendations(self, user_message: str, context_data: Dict = None) -> str:
        """Get AI recommendations based on user query and project context"""
        
        # Build context from project data
        context = ""
        if context_data:
            total_tasks = context_data.get('total_tasks', 0)
            completed_tasks = context_data.get('completed_tasks', 0)
            in_progress_tasks = context_data.get('in_progress_tasks', 0)
            
            context = f"""
Project Context:
- Total tasks: {total_tasks}
- Completed: {completed_tasks}
- In progress: {in_progress_tasks}
- Completion rate: {(completed_tasks/total_tasks*100) if total_tasks > 0 else 0:.1f}%
"""
        
        # Create a focused prompt for project management
        prompt = f"""You are a helpful project management assistant. {context}

User Question: {user_message}

Provide a helpful response about project management, task prioritization, or team collaboration:"""
        
        return self._call_huggingface_api(prompt, max_length=300)
    
    def analyze_team_performance(self, historical_data: Dict) -> str:
        """Analyze team performance and provide insights"""
        velocity = historical_data.get('average_tasks_per_sprint', 0)
        completion_rate = historical_data.get('completion_rate', 0)
        
        prompt = f"""Team Performance Analysis:

Sprint velocity: {velocity} tasks per sprint
Completion rate: {completion_rate}%

Provide insights and suggestions for team improvement:"""
        
        return self._call_huggingface_api(prompt, max_length=200)


# Alternative: Local AI using transformers (if you want to run locally)
class LocalAIService:
    def __init__(self):
        try:
            from transformers import pipeline
            # Use a smaller, faster model for local deployment
            self.generator = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                tokenizer="microsoft/DialoGPT-small"
            )
        except ImportError:
            self.generator = None
    
    def generate_response(self, prompt: str) -> str:
        if not self.generator:
            return "Local AI service is not available. Please install transformers: pip install transformers torch"
        
        try:
            response = self.generator(
                prompt,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )
            return response[0]['generated_text'][len(prompt):].strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"


# Fallback service with rule-based responses
class FallbackAIService:
    def __init__(self):
        self.responses = {
            'priority': [
                "Consider focusing on high-priority bugs first, then new features.",
                "I recommend tackling blocking issues before starting new development.",
                "Review dependencies between tasks to avoid bottlenecks."
            ],
            'sprint': [
                "For sprint planning, consider team capacity and historical velocity.",
                "Include a mix of bug fixes and new features in each sprint.",
                "Leave some buffer time for unexpected urgent tasks."
            ],
            'team': [
                "Good team collaboration starts with clear communication.",
                "Regular stand-ups help keep everyone aligned on priorities.",
                "Consider pair programming for complex tasks."
            ]
        }
    
    def get_response(self, user_message: str) -> str:
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['priority', 'important', 'urgent']):
            return self.responses['priority'][0]
        elif any(word in message_lower for word in ['sprint', 'planning', 'iteration']):
            return self.responses['sprint'][0]
        elif any(word in message_lower for word in ['team', 'collaboration', 'communication']):
            return self.responses['team'][0]
        else:
            return "I can help you with task prioritization, sprint planning, and team collaboration. What specific area would you like assistance with?"


# Main service that combines all approaches
class SmartAIService:
    def __init__(self):
        self.hf_service = AIAssistantService()
        self.local_service = LocalAIService()
        self.fallback_service = FallbackAIService()
    
    def get_ai_response(self, user_message: str, context_data: Dict = None) -> str:
        """Try multiple AI services in order of preference"""
        
        # Try Hugging Face first
        if self.hf_service.hf_api_key:
            try:
                response = self.hf_service.get_task_recommendations(user_message, context_data)
                if response and "error" not in response.lower() and len(response) > 20:
                    return response
            except Exception:
                pass
        
        # Try local AI as backup
        if self.local_service.generator:
            try:
                response = self.local_service.generate_response(f"Project management question: {user_message}")
                if response and len(response) > 10:
                    return response
            except Exception:
                pass
        
        # Use fallback rule-based responses
        return self.fallback_service.get_response(user_message)