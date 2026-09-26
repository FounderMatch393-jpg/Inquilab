"""
Ollama LLM Connector
Manages communication with Ollama local LLM service
"""
import os
import requests
from typing import Optional, List, Dict
import json

try:
    import inquilab_config as saved_config
except ImportError:
    saved_config = None

class OllamaConnector:
    """Connect to and communicate with Ollama LLM service."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        model: str = None,
        warmup_model: str = None,
        temperature: float = 0.0,
        timeout: int = 300,
        warmup_timeout: int = 60,
        *,
        small_model: str = None,
        large_model: str = None
    ):
        """
        Initialize Ollama connector.
        
        Args:
            host: Ollama host (default: localhost, from OLLAMA_HOST env var)
            port: Ollama port (default: 11434, from OLLAMA_PORT env var)
            model: Legacy alias for the large working model.
            warmup_model: Legacy alias for the small loading model.
            small_model: Model used to warm up Ollama (from OLLAMA_SMALL_MODEL or
                OLLAMA_WARMUP_MODEL).
            large_model: Model used for agent work (from OLLAMA_LARGE_MODEL or
                OLLAMA_MODEL).
            temperature: Model temperature (default: 0.0)
            timeout: Answer request timeout in seconds (default: 300)
            warmup_timeout: Warm-up request timeout in seconds (default: 60)
        """
        self.host = host or os.getenv(
            "OLLAMA_HOST",
            getattr(saved_config, "OLLAMA_HOST", "localhost"),
        )
        self.port = port or int(os.getenv(
            "OLLAMA_PORT",
            str(getattr(saved_config, "OLLAMA_PORT", 11434)),
        ))
        self.large_model = (
            large_model
            or model
            or os.getenv("OLLAMA_LARGE_MODEL")
            or os.getenv("OLLAMA_MODEL", getattr(saved_config, "OLLAMA_LARGE_MODEL", "llama3.2:latest"))
        )
        self.small_model = (
            small_model
            or warmup_model
            or os.getenv("OLLAMA_SMALL_MODEL")
            or os.getenv("OLLAMA_WARMUP_MODEL", getattr(saved_config, "OLLAMA_SMALL_MODEL", "tinyllama:latest"))
        )
        # Keep the old attributes available to callers using the original API.
        self.model = self.large_model
        self.warmup_model = self.small_model
        self.temperature = temperature if temperature != 0.0 else getattr(saved_config, "OLLAMA_TEMPERATURE", 0.0)
        self.timeout = timeout if timeout != 300 else getattr(saved_config, "OLLAMA_TIMEOUT", 300)
        self.warmup_timeout = warmup_timeout if warmup_timeout != 60 else getattr(saved_config, "OLLAMA_WARMUP_TIMEOUT", 60)
        self.base_url = f"http://{self.host}:{self.port}"
        
        self._connection_verified = False
    
    def verify_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            self._connection_verified = response.status_code == 200
            return self._connection_verified
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to Ollama at {self.base_url}")
            print("   Make sure Ollama is running: ollama serve")
            return False
        except Exception as e:
            print(f"❌ Error verifying Ollama connection: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return list(dict.fromkeys(models))  # Preserve tags and remove duplicates
            return []
        except Exception as e:
            print(f"❌ Error fetching available models: {e}")
            return []

    def warm_up(self) -> bool:
        """Load a small model before the larger answer model is used."""
        if not self.small_model or self.small_model == self.large_model:
            return True

        available_models = self.get_available_models()
        if self.small_model not in available_models:
            print(f"⚠️ Small model '{self.small_model}' is not installed; continuing with '{self.large_model}'.")
            print(f"   Install it with: ollama pull {self.small_model}")
            return True

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.small_model,
                    "prompt": "Reply with OK.",
                    "stream": False,
                    "options": {"num_predict": 1}
                },
                timeout=self.warmup_timeout
            )
            if response.status_code == 200:
                print(f"✅ Ollama loaded '{self.small_model}'. Working with '{self.large_model}'.")
                return True
            print(f"⚠️ Small model returned HTTP {response.status_code}; continuing with '{self.large_model}'.")
        except requests.exceptions.Timeout:
            print(f"⚠️ Small model timed out after {self.warmup_timeout}s; continuing with '{self.large_model}'.")
        except requests.exceptions.RequestException as exc:
            print(f"⚠️ Small model failed: {exc}; continuing with '{self.large_model}'.")
        return True
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama registry.
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📥 Pulling model '{model_name}' from Ollama registry...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600  # Longer timeout for downloads
            )
            
            if response.status_code == 200:
                print(f"✅ Model '{model_name}' pulled successfully!")
                return True
            else:
                print(f"❌ Failed to pull model: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error pulling model: {e}")
            return False
    
    def chat(self, messages: List[Dict], _model: str = None) -> Optional[str]:
        """
        Send a chat message to the Ollama model.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            Model response text, or None if error
        """
        if not self._connection_verified and not self.verify_connection():
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": _model or self.large_model,
                    "messages": messages,
                    "stream": True,
                    "temperature": self.temperature
                },
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Consume streamed JSONL first; calling response.json() first blocks
                # until a streamed response finishes.
                line_reader = getattr(response, "iter_lines", None)
                if callable(line_reader):
                    chunks = []
                    for line in line_reader(decode_unicode=True):
                        if not line:
                            continue
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content")
                        if chunk:
                            chunks.append(chunk)
                    if chunks:
                        return "".join(chunks)

                json_reader = getattr(response, "json", None)
                if callable(json_reader):
                    payload = json_reader()
                    message = payload.get("message", {})
                    if isinstance(message, dict) and "content" in message:
                        return message["content"]
                return None
            elif response.status_code == 404:
                print(f"❌ Large model '{self.large_model}' not found in Ollama")
                print(f"   Available models: {self.get_available_models()}")
                print(f"   To pull a model: ollama pull {self.large_model}")
                return None
            else:
                print(f"❌ Error from Ollama: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            if _model is None and self.small_model and self.small_model != self.large_model:
                print(f"Warning: model '{self.large_model}' timed out; retrying with '{self.small_model}'.")
                return self.chat(messages, _model=self.small_model)
            print(f"❌ Ollama request timed out after {self.timeout}s")
            print("   Try checking Ollama model performance or configuration")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ Lost connection to Ollama at {self.base_url}")
            self._connection_verified = False
            return None
        except Exception as e:
            print(f"❌ Error communicating with Ollama: {e}")
            return None
    
    def chat_streaming(self, messages: List[Dict]):
        """
        Send a chat message with streaming response.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Yields:
            Chunks of model response text
        """
        if not self._connection_verified and not self.verify_connection():
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.large_model,
                    "messages": messages,
                    "stream": True,
                    "temperature": self.temperature
                },
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            yield data["message"]["content"]
            else:
                print(f"❌ Error from Ollama: {response.text}")
                
        except Exception as e:
            print(f"❌ Error with streaming: {e}")
    
    def generate(self, prompt: str) -> Optional[str]:
        """
        Generate text from a prompt (non-chat mode).
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated text, or None if error
        """
        if not self._connection_verified and not self.verify_connection():
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.large_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": self.temperature
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                print(f"❌ Error from Ollama: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error generating text: {e}")
            return None
    
    def get_status(self) -> Dict:
        """
        Get Ollama service status and configuration.
        
        Returns:
            Status dictionary
        """
        status = {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "model": self.large_model,
            "large_model": self.large_model,
            "warmup_model": self.small_model,
            "small_model": self.small_model,
            "connected": self.verify_connection(),
            "available_models": self.get_available_models() if self.verify_connection() else []
        }
        return status
    
    def __repr__(self) -> str:
        return f"OllamaConnector(host={self.host}, port={self.port}, large_model={self.large_model}, small_model={self.small_model})"
