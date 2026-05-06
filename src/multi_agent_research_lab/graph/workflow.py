"""LangGraph workflow skeleton."""

from langgraph.graph import StateGraph, END
from multi_agent_research_lab.core.state import ResearchState

# Cần import các Agent của bạn (Giả định bạn đã tạo sườn class cho chúng)
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent

class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self):
        # Khởi tạo các tác nhân (agents)
        self.supervisor = SupervisorAgent()
        
        # Lưu ý: Các worker này sẽ được implement chi tiết ở Milestone 3
        # Tạm thời bạn cứ tạo file và class rỗng có hàm run() cho chúng nhé.
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        
        # Compile graph 1 lần khi khởi tạo object
        self.app = self.build()

    def build(self) -> object:
        """Create a LangGraph graph."""
        # 1. Khởi tạo Graph với cấu trúc State chung
        workflow = StateGraph(ResearchState)
        
        # 2. Thêm các Nodes (Tương ứng với mỗi Node là 1 Agent)
        workflow.add_node("Supervisor", self.supervisor.run)
        workflow.add_node("Researcher", self.researcher.run)
        workflow.add_node("Analyst", self.analyst.run)
        workflow.add_node("Writer", self.writer.run)
        
        # 3. Hàm Routing - Đọc quyết định của Supervisor để điều hướng
        def router(state: ResearchState) -> str:
            # Tuỳ thuộc vào việc ResearchState của bạn là dict hay Pydantic model
            # Dưới đây là cách an toàn để lấy giá trị next_agent
            if isinstance(state, dict):
                next_node = state.get("next_agent", "finish")
            else:
                next_node = getattr(state, "next_agent", "finish")
            
            # Mapping string thành tên Node đã khai báo ở trên
            if next_node == "researcher":
                return "Researcher"
            elif next_node == "analyst":
                return "Analyst"
            elif next_node == "writer":
                return "Writer"
            else:
                return END # Stop condition: Kết thúc Graph

        # 4. Định nghĩa Edges (Luồng đi)
        
        # Bắt buộc điểm vào (Entry Point) là Supervisor
        workflow.set_entry_point("Supervisor")
        
        # Từ Supervisor, kiểm tra hàm router để rẽ nhánh có điều kiện
        workflow.add_conditional_edges("Supervisor", router)
        
        # Sau khi các Worker hoàn thành công việc, BẮT BUỘC trả quyền điều khiển về cho Supervisor
        workflow.add_edge("Researcher", "Supervisor")
        workflow.add_edge("Analyst", "Supervisor")
        workflow.add_edge("Writer", "Supervisor")
        
        return workflow.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        
        print("[Workflow] ⚙️ Đang khởi chạy Multi-Agent Graph...")
        
        # Invoke sẽ chạy toàn bộ graph cho đến khi chạm END
        final_state = self.app.invoke(state)
        
        # Trả về state cuối cùng. Nếu LangGraph trả về dict, 
        # bạn có thể cần parse lại thành model tuỳ thuộc vào code base.
        if isinstance(final_state, dict) and not isinstance(state, dict):
            # Ví dụ nếu ResearchState là Pydantic Model:
            return ResearchState(**final_state)
            
            
        return final_state