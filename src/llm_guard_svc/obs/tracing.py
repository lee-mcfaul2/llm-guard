"""OTel tracer + FastAPI auto-instrumentation for llm-guard.

The gateway calls llm-guard via httpx, which propagates the W3C
`traceparent` header. With FastAPI auto-instrumentation enabled on
this side, the inbound /scan span becomes a child of the gateway's
`gateway.llm_guard.scan_inbound` (or scan_outbound) span -- meaning a
trace search in Tempo for a request_uuid shows all the llm-guard work
inline with the rest of the prompt's lifecycle.

If the OTLP endpoint is empty (tests, dev), the tracer provider is
installed but exports nothing. Manual span creation and attribute
setting still work, just silently.
"""
from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_PROVIDER: TracerProvider | None = None
_FASTAPI_INSTRUMENTOR: Any = None


def setup_tracing(endpoint: str, service_name: str) -> None:
    global _PROVIDER, _FASTAPI_INSTRUMENTOR
    if _PROVIDER is not None:
        return
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    _PROVIDER = provider
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        _FASTAPI_INSTRUMENTOR = FastAPIInstrumentor
    except ImportError:
        _FASTAPI_INSTRUMENTOR = None


def instrument_fastapi_app(app: object) -> None:
    if _FASTAPI_INSTRUMENTOR is None:
        return
    _FASTAPI_INSTRUMENTOR.instrument_app(app)  # type: ignore[attr-defined]


def set_attrs_on_current_span(**attrs: object) -> None:
    """Attach attributes to the active request span (created by auto-instr)."""
    s = trace.get_current_span()
    if s is None:
        return
    for k, v in attrs.items():
        s.set_attribute(k, v)  # type: ignore[arg-type]
