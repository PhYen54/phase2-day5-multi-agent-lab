"""Shared state for the multi-agent workflow.

Students should extend this file when adding new agents, outputs, or evaluation metrics.
"""

from ast import operator
from operator import add
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field

from multi_agent_research_lab.core.schemas import AgentResult, ResearchQuery, SourceDocument


class ResearchState(BaseModel):
    """Single source of truth passed through the workflow."""

    request: ResearchQuery
    iteration: int = 0
    # Thêm trường này để Router có thể đọc được quyết định của Supervisor
    next_agent: str = "finish" 
    
    # Sử dụng Annotated để LangGraph tự động append vào list thay vì overwrite
    route_history: Annotated[list[str], add] = Field(default_factory=list)
    sources: Annotated[list[SourceDocument], add] = Field(default_factory=list)
    
    research_notes: Optional[str] = None
    analysis_notes: Optional[str] = None
    final_answer: Optional[str] = None

    agent_results: Annotated[list[AgentResult], add] = Field(default_factory=list)
    trace: Annotated[list[dict[str, Any]], add] = Field(default_factory=list)
    errors: Annotated[list[str], add] = Field(default_factory=list)

    def record_route(self, route: str) -> None:
        self.route_history.append(route)
        self.iteration += 1

    def add_trace_event(self, name: str, payload: dict[str, Any]) -> None:
        self.trace.append({"name": name, "payload": payload})
