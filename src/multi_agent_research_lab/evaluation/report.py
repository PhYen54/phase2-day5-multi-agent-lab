"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


"""Evaluation report generator."""

# Giả định import model BenchmarkMetrics từ file của bạn
# from multi_agent_research_lab.models import BenchmarkMetrics

def render_markdown_report(metrics: list) -> str:
    """Render benchmark metrics to a rich markdown report.
    
    Tự động xuất bảng chi tiết, tính toán số liệu trung bình và tạo template phân tích.
    """
    
    if not metrics:
        return "# Benchmark Report\n\nKhông có dữ liệu để hiển thị."

    # 1. Tính toán các chỉ số trung bình (Aggregates)
    total_runs = len(metrics)
    avg_latency = sum(getattr(m, 'latency_seconds', 0) for m in metrics) / total_runs
    avg_cost = sum(getattr(m, 'cost_usd', getattr(m, 'estimated_cost_usd', 0)) for m in metrics) / total_runs
    
    # Lọc ra các run không bị lỗi để tính điểm trung bình chính xác hơn
    valid_runs = [m for m in metrics if getattr(m, 'failure_rate', 0) < 1.0]
    avg_quality = sum(getattr(m, 'quality_score', 0) for m in valid_runs) / len(valid_runs) if valid_runs else 0
    avg_citation = sum(getattr(m, 'citation_coverage', 0) for m in valid_runs) / len(valid_runs) if valid_runs else 0
    failure_rate_overall = (total_runs - len(valid_runs)) / total_runs * 100

    # 2. Xây dựng phần Header và Tổng quan (Summary)
    lines = [
        "# 📊 Benchmark Report: Multi-Agent Research System",
        "",
        "## 1. Tổng Quan Hiệu Suất (Executive Summary)",
        f"- **Tổng số ca kiểm thử (Runs):** {total_runs}",
        f"- **Tỷ lệ thất bại chung:** {failure_rate_overall:.1f}%",
        f"- **Thời gian trung bình (Latency):** {avg_latency:.2f} s",
        f"- **Chi phí trung bình (Cost):** ${avg_cost:.4f}",
        f"- **Điểm chất lượng trung bình (Quality):** {avg_quality:.1f}/10",
        f"- **Tỷ lệ trích dẫn trung bình (Citation):** {avg_citation * 100:.1f}%",
        "",
        "## 2. Kết Quả Chi Tiết (Detailed Metrics)",
        "",
        "| Run Name | Latency (s) | Cost (USD) | Quality (0-10) | Citation | Status |",
        "|---|---:|---:|---:|---:|---|"
    ]

    # 3. Lặp qua từng kết quả để đưa vào bảng
    for item in metrics:
        run_name = getattr(item, 'run_name', 'Unknown')
        latency = f"{getattr(item, 'latency_seconds', 0):.2f}"
        
        # Xử lý an toàn cho cost (tương thích ngược với stub cũ của bạn)
        cost_val = getattr(item, 'cost_usd', getattr(item, 'estimated_cost_usd', 0))
        cost = f"${cost_val:.4f}" if cost_val is not None else "N/A"
        
        quality_val = getattr(item, 'quality_score', None)
        quality = f"{quality_val:.1f}" if quality_val is not None else "N/A"
        
        citation_val = getattr(item, 'citation_coverage', 0)
        citation = f"{citation_val * 100:.0f}%"
        
        failure_val = getattr(item, 'failure_rate', 0)
        status = "❌ Fail" if failure_val >= 1.0 else "✅ Pass"

        lines.append(f"| **{run_name}** | {latency} | {cost} | {quality} | {citation} | {status} |")

    # 4. Thêm phần Trace Links và Template cho Exit Ticket
    lines.extend([
        "",
        "## 3. Observability & Traces",
        "Để xem chi tiết log, prompt/response và token usage của từng agent:",
        "- **LangSmith:** Truy cập [smith.langchain.com](https://smith.langchain.com/) -> Chọn project `multi-agent-research-lab`.",
        "- **Local Logs:** Kiểm tra file `traces.jsonl` trong thư mục gốc.",
        "",
        "---",
        "## 4. Exit Ticket (Phân tích của nhóm)",
        "*TODO(student): Dựa vào bảng số liệu trên, hãy trả lời 2 câu hỏi sau:*",
        "",
        "**Câu 1: Case nào nên dùng multi-agent? Vì sao?**",
        "> *Ghi câu trả lời của bạn vào đây... (Gợi ý: Nhìn vào điểm Quality và Citation khi task phức tạp)*",
        "",
        "**Câu 2: Case nào không nên dùng multi-agent? Vì sao?**",
        "> *Ghi câu trả lời của bạn vào đây... (Gợi ý: Nhìn vào Latency và Cost khi câu hỏi quá đơn giản)*"
    ])

    return "\n".join(lines) + "\n"
