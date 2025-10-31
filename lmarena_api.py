import requests
import json
import uuid
from typing import Generator, Optional


class LMArenaAPI:
    def __init__(self):
        self.base_url = "https://lmarena.ai"
        self.api_url = f"{self.base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        })
        self.conversation_id = None
        
    def get_models(self):
        """Get available AI models"""
        return [
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "gemini-pro",
            "llama-2-70b",
            "mixtral-8x7b",
        ]
    
    def create_conversation(self):
        """Create a new conversation"""
        self.conversation_id = str(uuid.uuid4())
        return self.conversation_id
    
    def chat(self, message: str, model: str = "gpt-3.5-turbo") -> Generator[str, None, None]:
        """
        Send a chat message and stream the response
        
        Args:
            message: The user message
            model: The AI model to use
            
        Yields:
            Response chunks from the AI
        """
        if not self.conversation_id:
            self.create_conversation()
        
        try:
            url = f"{self.api_url}/chat"
            
            payload = {
                "message": message,
                "model": model,
                "conversation_id": self.conversation_id,
                "stream": True
            }
            
            response = self.session.post(
                url,
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'content' in data:
                                    yield data['content']
                                elif 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
            else:
                yield f"Error: API returned status code {response.status_code}"
                
        except requests.exceptions.Timeout:
            yield "Error: Request timed out"
        except requests.exceptions.RequestException as e:
            yield f"Error: {str(e)}"
    
    def chat_simple(self, message: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Send a chat message and get the full response
        
        Args:
            message: The user message
            model: The AI model to use
            
        Returns:
            Full response from the AI
        """
        response_text = ""
        for chunk in self.chat(message, model):
            response_text += chunk
        return response_text
    
    def reset_conversation(self):
        """Reset the current conversation"""
        self.conversation_id = None
