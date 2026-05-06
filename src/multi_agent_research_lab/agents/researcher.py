"""Researcher agent skeleton."""
import json
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self):
        # Tùy thuộc vào BaseAgent có khởi tạo sẵn gì không, bạn có thể gọi super()
        # super().__init__()
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> dict:
        """Populate `state.sources` and `state.research_notes`."""
        
        # 1. Trích xuất query từ State
        query = state.request.query
        
        print(f"\n[🔍 {self.name.capitalize()}] Đang tìm kiếm thông tin cho: '{query}'...")

        system_prompt = """You are an expert Research Assistant.
Your task is to find comprehensive, accurate, and factual information based on the user's query.
You must gather key facts, statistics, and main points, and provide citations.

CRITICAL: You must respond in STRICT VALID JSON format matching this schema:
{
    "sources": [
        {
            "title": "Source 1 Title", 
            "url": "https://example.com/1",
            "snippet": "A brief 1-2 sentence summary of this source's relevance." 
        }
    ],
    "research_notes": "Detailed raw notes, bullet points, and facts gathered from the sources."
}
Do not include any Markdown formatting like 
```json or any conversational text outside the JSON object."""

        user_prompt = f"Research Query: {query}"

        try:
            # 3. Gọi LLM
            response = self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            response_text = response.content.strip()
            
            # Xử lý dọn dẹp nếu LLM lỡ tay trả về block code markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            # 4. Parse JSON
            data = json.loads(response_text)
            
            sources = data.get("sources", [])
            research_notes = data.get("research_notes", "No notes generated.")

            print(f"[🔍 {self.name.capitalize()}] ✅ Tìm thấy {len(sources)} nguồn tài liệu và hoàn tất ghi chú.")

            # 5. TRẢ VỀ DIFF (DICTIONARY) THAY VÌ TRẢ VỀ TOÀN BỘ STATE
            # Đồng thời chỉ định next_agent là supervisor để trao quyền điều phối lại
            return {
                "sources": sources,
                "research_notes": research_notes,
                "next_agent": "supervisor" 
            }

        except json.JSONDecodeError as e:
            print(f"[🔍 {self.name.capitalize()}] ❌ Lỗi parse JSON từ LLM: {e}")
            return {
                "research_notes": "Error: LLM failed to return structured JSON data.",
                "next_agent": "supervisor"
            }
        except Exception as e:
            print(f"[🔍 {self.name.capitalize()}] ❌ Lỗi hệ thống: {e}")
            return {
                "next_agent": "supervisor",
                "errors": [f"Researcher Error: {str(e)}"]
            }