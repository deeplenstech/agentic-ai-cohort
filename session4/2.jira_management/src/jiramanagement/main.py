#!/usr/bin/env python
import os
import base64
import warnings
import asyncio
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

import logging
logging.getLogger("opentelemetry.sdk._shared_internal").setLevel(logging.CRITICAL)

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
    headers={"Authorization": f"Basic {auth_header}"},
    timeout=5,
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
from . llm_otel_listener import LLMOtelListener

LLMOtelListener()

from crewai_tools import MCPServerAdapter
from . crew import create_crew

async def main():
    tracer = otel_trace.get_tracer("jira_management")
    inputs = {
        'jira_request': (
            "I have a todo app. Based on the requirements confluence page create one epic "
            "in the project with the ID 'TIME' in the cloud ID: 'https://deeplenstech.atlassian.net'. "
            "Based on the requirements confluence page, also create tasks with the parent as the newly created epic. "
            "Task dependencies should be effectively set after the tasks have been created. "
            "Epic requirements confluence page: "
            "https://deeplenstech.atlassian.net/wiki/spaces/~557058fd5ab0b1dd344900a0675e1db1567b47/pages/360449/Reminder+feature+in+my+ToDo+app \n"
            "After you are done with the changes, update the confluence page and add a section containing "
            "a table of newly created jira issues along with their summary"
        )
    }

    with tracer.start_as_current_span("jira_management") as span:
        try:
            span.set_attribute("input", str(inputs))
            response = create_crew().kickoff(inputs=inputs).raw
            print(response)
            span.set_attribute("output", str(response or ""))
        except Exception as e:
            span.record_exception(e)
            raise Exception(f"An error occurred while running the crew: {e}")
        finally:
            try:
                provider.force_flush(timeout_millis=5000)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
