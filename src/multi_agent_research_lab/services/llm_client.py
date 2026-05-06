"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass

from multi_agent_research_lab.core.errors import StudentTodoError
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from multi_agent_research_lab.observability.tracing import trace_span

# Load biến môi trường từ file .env
load_dotenv()

@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None

class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def __init__(self):
        # Khởi tạo OpenAI client. 
        # Nó sẽ tự động tìm biến OPENAI_API_KEY trong environment variables (được load từ .env)
        # Tích hợp sẵn retry và timeout ở cấp độ client.
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=3,
            timeout=60.0
        )
        self.model = "gpt-4o-mini"

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
  
    
        try:
            # Bắt đầu Trace Span
            with trace_span("OpenAI_Call", {"model": self.model, "system": system_prompt, "user": user_prompt}) as span:
                
                # 1. Gọi API tới OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2, # Giúp câu trả lời fact-based hơn
                )
                
                # 2. Trích xuất nội dung text
                text_content = response.choices[0].message.content
                
                # 3. Tính toán Token Usage NGAY TẠI ĐÂY (trước khi gán vào span)
                usage = response.usage
                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0
                
                # 4. Ghi nhận Token vào Span (Bây giờ biến đã có giá trị)
                span["attributes"]["tokens"] = {
                    "prompt": prompt_tokens, 
                    "completion": completion_tokens
                }
                
                # 5. Trả về kết quả
                return LLMResponse(
                        content=text_content,
                        input_tokens=prompt_tokens,       # <-- Sửa chữ prompt_tokens thành input_tokens
                        output_tokens=completion_tokens   # <-- Sửa chữ completion_tokens thành output_tokens
                        # cost_usd không cần truyền vào vì nó đã có mặc định là None
                    )
                
        except Exception as e:
            print(f"[LLMClient] Call Failed: {str(e)}")
            raise e
def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """
    Hàm wrapper giúp tương thích với logic trong cli.py.
    Trả về dict thay vì Pydantic object để dễ dàng dùng .get()
    """
    client = LLMClient()
    response = client.complete(system_prompt, user_prompt)
    
    return {
        "text": response.content,
        "usage": {
            "prompt_tokens": response.input_tokens,
            "completion_tokens": response.output_tokens,
            "total_tokens": (response.input_tokens or 0) + (response.output_tokens or 0)
        },
        "cost": response.cost_usd
    }