"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

import re
from time import perf_counter
Runner = Callable[[str], ResearchState]

def _evaluate_quality_with_llm(query: str, final_answer: str) -> float:
    """Sử dụng LLM để chấm điểm tự động bài viết (Peer Review thay thế)."""
    
    # Import LLMClient của bạn
    from multi_agent_research_lab.services.llm_client import LLMClient
    
    system_prompt = """You are an expert peer reviewer grading a research assistant's answer.
Evaluate the answer based on the following rubric (0-10 scale):
- Accuracy (Are the facts correct and addressing the query?)
- Clarity (Is it easy to read and well-structured?)
- Objectivity (Does it present unbiased insights?)

CRITICAL: You must return ONLY a single number from 0 to 10 (e.g., 8.5). Do not include any text, explanation, or markdown."""

    user_prompt = f"Query: {query}\n\nAnswer to grade:\n{final_answer}"
    
    try:
        llm = LLMClient()
        response = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        
        # Ép kiểu kết quả LLM trả về thành số float
        score_text = response.content.strip()
        # Dọn dẹp nếu LLM lỡ thêm ký tự lạ
        score = float(re.findall(r"[-+]?\d*\.\d+|\d+", score_text)[0])
        
        # Đảm bảo điểm nằm trong khoảng 0-10
        return max(0.0, min(10.0, score))
        
    except Exception as e:
        print(f"[LLM Judge Error] Không thể chấm điểm: {e}")
        return 0.0 # Nếu LLM lỗi, trả về 0
    
def run_benchmark(run_name: str, query: str, runner: callable) -> tuple[object, BenchmarkMetrics]:
    """Measure metrics across latency, cost, quality, citations, and error rate."""

    print(f"\n[Benchmark] ⏳ Đang chạy test case: '{run_name}'...")
    started = perf_counter()
    
    try:
        # 1. Chạy Agent Workflow
        state = runner(query)
        latency = perf_counter() - started
        
        # Kiểm tra xem có lấy được final_answer không
        final_answer = ""
        if isinstance(state, dict):
            final_answer = state.get("final_answer", "")
        else:
            final_answer = getattr(state, "final_answer", "")

        # 2. Tính Failure Rate
        # Thất bại nếu không có câu trả lời, hoặc câu trả lời chứa thông báo lỗi hệ thống
        is_failure = False
        if not final_answer or "Error:" in final_answer or "Lỗi:" in final_answer:
            is_failure = True
            
        failure_rate = 1.0 if is_failure else 0.0

        # 3. Tính Cost (Token Usage)
        # Tùy thuộc vào cách bạn log token ở Milestone trước. 
        # Giả sử ta ước lượng chi phí của GPT-4o-mini (Input: $0.15/1M, Output: $0.6/1M)
        # Nếu chưa lưu token vào state, có thể tính xấp xỉ: 1 token ~ 4 chars
        cost_usd = 0.15
        if not is_failure:
            approx_tokens = len(str(state)) / 4 
            cost_usd = (approx_tokens / 1000000) * 0.6  # Ước tính thô để làm placeholder

        # 4. Tính Citation Coverage (Heuristic bằng Regex)
        # Đếm số câu (claims) và số lượng trích dẫn dạng [1], [2]
        citation_coverage = 0.0
        if not is_failure:
            sentences = [s for s in final_answer.split('.') if len(s.strip()) > 15]
            citations = re.findall(r'\[\d+\]', final_answer)
            
            total_claims = len(sentences) if len(sentences) > 0 else 1
            # Tỷ lệ coverage (giới hạn tối đa là 1.0)
            citation_coverage = min(len(citations) / total_claims, 1.0)

        # 5. Tính Quality Score (0-10) bằng LLM-as-a-Judge
        quality_score = 0.0
        if not is_failure:
            quality_score = _evaluate_quality_with_llm(query, final_answer)

        # Đóng gói Metrics
        metrics = BenchmarkMetrics(
            run_name=run_name,
            latency_seconds=latency,
            cost_usd=cost_usd,
            quality_score=quality_score,
            citation_coverage=citation_coverage,
            failure_rate=failure_rate
        )
        
        print(f"[Benchmark] ✅ Hoàn thành! Quality: {quality_score}/10 | Latency: {latency:.2f}s")
        return state, metrics

    except Exception as e:
        # Nếu code crash hoàn toàn
        latency = perf_counter() - started
        print(f"[Benchmark] ❌ Thất bại (Crash): {str(e)}")
        
        # Trả về metrics thất bại toàn tập
        metrics = BenchmarkMetrics(
            run_name=run_name,
            latency_seconds=latency,
            cost_usd=0.0,
            quality_score=0.0,
            citation_coverage=0.0,
            failure_rate=1.0
        )
        return None, metrics