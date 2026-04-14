#!/usr/bin/env python
import os
import base64
import warnings
import asyncio
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Set up OTEL -> Langfuse exporter BEFORE crewai imports
langfuse_public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
langfuse_secret_key = os.environ["LANGFUSE_SECRET_KEY"]
langfuse_host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
auth_header = base64.b64encode(f"{langfuse_public_key}:{langfuse_secret_key}".encode()).decode()

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry import trace as otel_trace

exporter = OTLPSpanExporter(
    endpoint=f"{langfuse_host}/api/public/otel/v1/traces",
    headers={"Authorization": f"Basic {auth_header}"}
)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(exporter))
otel_trace.set_tracer_provider(provider)

# Instrument CrewAI orchestration spans (agents, tasks, crew)
from openinference.instrumentation.crewai import CrewAIInstrumentor
CrewAIInstrumentor().instrument()

# Subscribe to CrewAI's event bus to create OTEL spans for LLM calls.
# CrewAI 0.186+ uses provider-native SDKs (e.g. AnthropicCompletion) and
# bypasses litellm entirely, so litellm instrumentation has no effect.
# The event bus is the only reliable hook into LLM calls at this version.
from stockresearch.llm_otel_listener import LLMOtelListener

LLMOtelListener()

from stockresearch.crewWithPlanner import crew


async def main():
    tracer = otel_trace.get_tracer("stockresearch")
    inputs = {
        'user_query': "Compare Google's current stock price to last month's price."
    }

    with tracer.start_as_current_span("stock-research") as span:
        try:
            span.set_attribute("input", str(inputs))
            response = crew.kickoff(inputs=inputs).raw
            print(response)
            span.set_attribute("output", str(response or ""))
        except Exception as e:
            span.record_exception(e)
            raise Exception(f"An error occurred while running the crew: {e}")
        finally:
            provider.force_flush()


if __name__ == "__main__":
    asyncio.run(main())
