import ollama
import json
import time
from typing import Optional, Any
from pydantic import BaseModel
from rich import print

class LLMClient:
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=host)

    def chat(self, messages: list[dict], format: Optional[str] = None) -> tuple[str, int, float]:
        """
        Gửi tin nhắn đến Ollama và trả về (nội dung, token_count, latency_ms).
        """
        start_time = time.time()
        
        try:
            if format == "json":
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    format="json"
                )
            else:
                response = self.client.chat(
                    model=self.model,
                    messages=messages
                )
        except Exception as e:
            if "ConnectionError" in str(type(e)) or "ConnectError" in str(e):
                print("\n[bold red]Lỗi kết nối đến Ollama![/bold red]")
                print("1. Hãy đảm bảo Ollama đã được cài đặt và đang chạy.")
                print("2. Chạy lệnh: [green]ollama serve[/green] hoặc mở ứng dụng Ollama.")
                print("3. Kiểm tra xem model đã được tải về chưa: [green]ollama pull " + self.model + "[/green]\n")
            raise e
            
        latency_ms = (time.time() - start_time) * 1000
        content = response['message']['content']
        
        total_tokens = response.get('eval_count', 0) + response.get('prompt_eval_count', 0)
        
        return content, total_tokens, latency_ms

    def structured_chat(self, messages: list[dict], schema: type[BaseModel]) -> tuple[Any, int, float]:
        """
        Gửi tin nhắn và parse kết quả theo schema Pydantic.
        """
        content, tokens, latency = self.chat(messages, format="json")
        try:
            data = json.loads(content)
            return schema.model_validate(data), tokens, latency
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Content: {content}")
            # Fallback or raise
            raise e
