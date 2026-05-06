"""Writer agent skeleton."""

import json
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self):
        self.llm = LLMClient()

    def run(self, state: ResearchState) -> dict:
        """Populate `state.final_answer`."""
        
        # Trích xuất toàn bộ dữ liệu từ State đã được các Agent trước thu thập
        query = state.request.query
        research_notes = state.research_notes or "No research notes available."
        analysis_notes = state.analysis_notes or "No analysis notes available."
        sources = state.sources

        print(f"\n[✍️  {self.name.capitalize()}] Đang chắp bút viết câu trả lời cuối cùng...")

        # 2. XỬ LÝ LỖI Pydantic Serialization
        # Chuyển đổi list Object thành list Dict trước khi cho vào json.dumps
        sources_dict = [s.model_dump() for s in sources] if sources else []

        system_prompt = """You are an expert Technical Writer and Editor.
Your task is to write a comprehensive, engaging, and well-structured final answer to the user's query.
You will be provided with raw research notes and synthesized analysis notes.

Guidelines:
1. Base your answer STRICTLY on the provided notes. Do not hallucinate external facts.
2. Incorporate the insights and structured points from the Analyst (e.g., contrasting viewpoints, key claims).
3. Use inline citations like [1], [2] when stating facts to back up your claims.
4. Format your output beautifully using Markdown (headers, bullet points, bold text).
5. ALWAYS provide a 'References' section at the very end listing the provided sources with their URLs.
6. Output ONLY the final article. Do not include any internal monologue, conversational filler, or JSON wrappers."""

        user_prompt = f"""
Original User Query: {query}

Analyst's Insights (Structure & Logic):
{analysis_notes}

Raw Research Notes (Facts & Details):
{research_notes}

Available Sources for Citation:
{json.dumps(sources_dict, indent=2, ensure_ascii=False)}
"""

        try:
            # Gọi LLM để viết bài
            response = self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            final_text = response.content.strip()
            
            print(f"[✍️  {self.name.capitalize()}] ✅ Đã hoàn tất bản thảo cuối cùng!")

            # 3. TRẢ VỀ DICT (DIFF) THAY VÌ TRẢ VỀ TOÀN BỘ STATE
            return {
                "final_answer": final_text,
                "next_agent": "supervisor" # Báo cáo lại cho Supervisor là đã làm xong
            }

        except Exception as e:
            print(f"[✍️  {self.name.capitalize()}] ❌ Lỗi hệ thống khi viết bài: {e}")
            return {
                "final_answer": f"Xin lỗi, tôi gặp lỗi trong quá trình tổng hợp câu trả lời: {str(e)}",
                "next_agent": "supervisor"
            }