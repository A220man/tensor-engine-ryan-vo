import os
from contextlib import asynccontextmanager
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from app.core.config import get_settings


_tracer_provider: TracerProvider | None = None


def init_telemetry(app=None) -> None:
    global _tracer_provider
    settings = get_settings()

    resource = Resource.create({SERVICE_NAME: settings.OTEL_SERVICE_NAME})
    _tracer_provider = TracerProvider(resource=resource)

    otlp_endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(_tracer_provider)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()


def get_tracer(name: str):
    return trace.get_tracer(name)


@asynccontextmanager
async def traced_session(name: str):
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise


def shutdown_telemetry() -> None:
    global _tracer_provider
    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None