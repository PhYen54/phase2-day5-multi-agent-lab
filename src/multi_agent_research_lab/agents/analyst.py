"""Analyst agent skeleton."""
import json
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self):
        self.llm = LLMClient()

    import json

    # 1. Đổi kiểu trả về thành dict
    def run(self, state: ResearchState) -> dict:
        """Populate `state.analysis_notes`."""
        
        # Trích xuất dữ liệu từ State
        query = state.request.query
        research_notes = state.research_notes or ""
        sources = state.sources

        print(f"\n[📊 {self.name.capitalize()}] Đang phân tích dữ liệu và trích xuất insights...")

        # 2. Sửa lỗi return state khi không có dữ liệu
        if not research_notes or research_notes == "No notes generated.":
            return {
                "analysis_notes": "Lỗi: Không có dữ liệu thô (research notes) để phân tích.",
                "next_agent": "supervisor"
            }
            
        sources_dict = [s.model_dump() for s in sources]
        
        system_prompt = """You are an expert Data Analyst and Critical Thinker. 
Your task is to analyze the raw research notes provided and synthesize them into structured insights.

CRITICAL: You must respond in STRICT VALID JSON format. 
The JSON must contain the 'analysis_notes' key, which should be a well-formatted string (can use Markdown inside the string) covering:
1. Key claims or arguments.
2. Comparison of different viewpoints or contradictions.
3. Flags for weak evidence or missing context.

SCHEMA:
{
    "analysis_notes": "### 1. Key Claims\\n- Point A...\\n### 2. Comparisons...\\n### 3. Weak Evidence...",
    "next_agent": "supervisor"
}

Do not include any Markdown formatting like ```json or any conversational text outside the JSON object."""
        
        user_prompt = f"""
Original Query: {query}

Raw Research Notes:
{research_notes}

Sources provided:
{json.dumps(sources_dict, indent=2, ensure_ascii=False)}
"""

        try:
            # Gọi LLM
            response = self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            response_text = response.content.strip()
            
            # Xử lý dọn dẹp markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            # Parse JSON
            data = json.loads(response_text)
            
            # 3. SỬA LỖI LOGIC: Trích xuất trực tiếp string Markdown mà AI đã viết sẵn
            analysis_formatted = data.get("analysis_notes", "No analysis notes generated.")

            print(f"[📊 {self.name.capitalize()}] ✅ Phân tích hoàn tất. Đã tạo structured insights.")

            # 4. TRẢ VỀ DICT ĐỂ LANGGRAPH TỰ ĐỘNG CẬP NHẬT STATE
            return {
                "analysis_notes": analysis_formatted,
                "next_agent": "supervisor"
            }

        except json.JSONDecodeError as e:
            print(f"[📊 {self.name.capitalize()}] ❌ Lỗi parse JSON từ LLM: {e}")
            return {
                "analysis_notes": f"Error: Analyst failed to structure the data. Raw output: {response_text}",
                "next_agent": "supervisor"
            }
        except Exception as e:
            print(f"[📊 {self.name.capitalize()}] ❌ Lỗi hệ thống: {e}")
            return {
                "analysis_notes": f"Error: {str(e)}",
                "next_agent": "supervisor"
            }