"""Supervisor / router skeleton."""

import re
import json

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self):
        self.llm = LLMClient()

    def _clean_json_string(self, raw_string: str) -> str:
        """Loại bỏ Markdown code blocks và khoảng trắng thừa."""
        # Tìm nội dung bên trong cặp ```json ... ``` hoặc ``` ... ```
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_string)
        if json_match:
            return json_match.group(1).strip()
        return raw_string.strip()

    def run(self, state: ResearchState) -> ResearchState:
        """
        Đánh giá trạng thái hiện tại và quyết định agent tiếp theo.
        """
        print("[Supervisor] Đang suy nghĩ bước tiếp theo...")
        
        system_prompt = """You are a Supervisor in a research team.

Your team members are:

- 'researcher': Search for facts and raw data.

- 'analyst': Synthesize data, compare, and extract insights.

- 'writer': Write the final comprehensive answer based on analysis.

- 'finish': If the final answer is already written and meets the user's requirement.

Always start with 'researcher' if no research notes exist yet. Then proceed to 'analyst' if research is done but no analysis. Then 'writer' if analysis is complete. Choose 'finish' only when a final answer exists.

Based on the current state of the research, who should act next?

Respond in strictly JSON format: {"next_agent": "researcher" | "analyst" | "writer" | "finish", "reason": "why"}"""

        # 1. Trích xuất bối cảnh
        query = state.request.query
        research_data = state.research_notes or "None"
        analysis_data = state.analysis_notes or "None"
        final_answer = state.final_answer or "None"
        step_count = state.iteration

        user_prompt = f"""
Original Query: {query}
Current Data Gathered: {research_data}
Current Analysis: {analysis_data}
Final Draft: {final_answer}
Step Count: {step_count}
"""
        try:
            response = self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            
            # 1. Lấy nội dung thô
            raw_content = response.content
            
            # 2. Vệ sinh chuỗi trước khi parse
            clean_content = self._clean_json_string(raw_content)
            
            # 3. Parse JSON
            decision = json.loads(clean_content)
            
            next_agent = decision.get("next_agent", "finish").lower().strip()
            reason = decision.get("reason", "")
            
            print(f"[Supervisor] Quyết định: Điều hướng tới -> {next_agent.upper()} (Lý do: {reason})")
            
            # Update state
            state.record_route(next_agent)
            state.next_agent = next_agent
            
            return {
                "next_agent": next_agent,
                "iteration": state.iteration + 1,
                "route_history": [next_agent] # LangGraph sẽ tự động append chữ này vào list cũ
            }
            
        except Exception as e:
            # In ra nội dung AI trả về để debug nếu vẫn lỗi
            print(f"[Supervisor] ❌ Lỗi parse. Nội dung AI trả về: {response.content[:100]}...")
            print(f"[Supervisor] Chi tiết lỗi: {e}")
            state.record_route("finish")
            return state
            