"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

# Import LangSmith (Yêu cầu phải có LANGCHAIN_API_KEY trong môi trường)
from langsmith.run_trees import RunTree

@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context using LangSmith RunTree for observability."""

    started = perf_counter()
    span_data: dict[str, Any] = {
        "name": name, 
        "attributes": attributes or {}, 
        "duration_seconds": None,
        "status": "running"
    }

    # 1. Khởi tạo một "nhánh" (RunTree) trên LangSmith
    # Nó sẽ tự động bắt dự án từ biến môi trường LANGCHAIN_PROJECT
    run_tree = RunTree(
        name=name,
        run_type="chain", # Có thể là "llm", "tool", hoặc "chain"
        inputs=attributes or {},
    )

    try:
        # 2. Chạy khối code bên trong with trace_span(...)
        yield span_data
        
        # Nếu thành công, kết thúc RunTree và đẩy lên server
        span_data["status"] = "success"
        run_tree.end(outputs={"status": "success", "final_attributes": span_data.get("attributes")})
        run_tree.post()

    except Exception as e:
        # Nếu có lỗi, ghi nhận lỗi vào LangSmith
        span_data["status"] = "error"
        span_data["error_message"] = str(e)
        run_tree.end(error=str(e))
        run_tree.post()
        raise e

    finally:
        # Ghi nhận latency cục bộ (nếu cần dùng cho benchmark.py sau này)
        span_data["duration_seconds"] = perf_counter() - started