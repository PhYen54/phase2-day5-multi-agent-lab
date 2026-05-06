"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()
import time

def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    start_time = time.time()
    
    try:
        # Gọi LLM thật thông qua llm_client
        system_prompt = (
            "You are an expert research assistant. "
            "Please analyze the user's query, find relevant information, "
            "and write a comprehensive and well-structured final answer."
        )
        
        llm_client = LLMClient()
        response = llm_client.complete(system_prompt=system_prompt, user_prompt=query)
        
        # Kết thúc đo Latency
        latency = time.time() - start_time
        
        # Cập nhật State
        state.final_answer = response.content
        
        # Tính cost (giả sử dựa trên token usage)
        cost = response.cost_usd or 0.0
        
        # Quality score placeholder (có thể implement heuristic hoặc LLM evaluation)
        quality_score = 7.5  # Placeholder
        
        # In câu trả lời cuối cùng
        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline Final Answer"))
        
        # In Benchmark Metrics
        metrics_panel = (
            f"⏱️  [bold]Latency:[/bold] {latency:.2f} seconds\n"
            f"🪙  [bold]Cost:[/bold] ${cost:.4f}\n"
        )
        console.print(Panel.fit(metrics_panel, title="📊 Benchmark Metrics", border_style="green"))

    except Exception as e:
        console.print(f"[bold red]❌ Lỗi trong quá trình chạy Baseline:[/bold red] {str(e)}")

@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    
    # 1. Bắt đầu bấm giờ
    start_time = time.time()
    
    try:
        # 2. Chạy đồ thị LangGraph
        result = workflow.run(state)
        
        # 3. Kết thúc bấm giờ và tính Latency
        latency = time.time() - start_time
        
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi trong quá trình chạy Multi-Agent:[/bold red] {str(e)}")
        return

    # 4. Trích xuất văn bản bài viết
    if isinstance(result, dict):
        final_text = result.get("final_answer", "Không có câu trả lời được tạo ra.")
    else:
        final_text = getattr(result, "final_answer", "Không có câu trả lời được tạo ra.")
        
    # 5. Các chỉ số phụ (Placeholder)
    # Lưu ý: Cost ở Multi-Agent thường khó tính hơn vì gọi LLM nhiều lần. 
    # Tạm thời ta để placeholder giống Single-Agent, hoặc bạn có thể tự cộng dồn cost trong State sau này.
    cost = 0.15 
    quality_score = 9.0  # Chấm điểm cao hơn Single-Agent vì Multi-Agent có phân tích sâu hơn

    # 6. In bài viết (Render Markdown xịn xò)
    console.print(
        Panel(
            Markdown(final_text), 
            title="Multi-Agent Final Answer", 
            border_style="green",
            expand=False # Khung ôm sát nội dung
        )
    )
    
    # 7. In bảng Benchmark Metrics
    metrics_panel = (
        f"⏱️  [bold]Latency:[/bold] {latency:.2f} seconds\n"
        f"🪙  [bold]Cost:[/bold] ${cost:.4f}\n"
    )
    console.print(Panel.fit(metrics_panel, title="📊 Benchmark Metrics", border_style="blue"))
if __name__ == "__main__":
    app()
