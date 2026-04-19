import json
from opentelemetry import trace as otel_trace
from opentelemetry.context import get_current
from crewai.events import (
    BaseEventListener,
    LLMCallStartedEvent,
    LLMCallCompletedEvent,
    LLMCallFailedEvent,
)

# Langfuse native OTEL attribute keys — using these lets Langfuse recognise the
# span as a generation and auto-consolidate token usage at the trace level.
_OBSERVATION_TYPE      = "langfuse.observation.type"
_OBSERVATION_INPUT     = "langfuse.observation.input"
_OBSERVATION_OUTPUT    = "langfuse.observation.output"
_OBSERVATION_MODEL     = "langfuse.observation.model.name"
_OBSERVATION_USAGE     = "langfuse.observation.usage_details"

# Internal event metadata fields — not useful as span attributes
_SKIP_FIELDS = {
    "timestamp", "type", "source_fingerprint", "source_type",
    "fingerprint_metadata", "event_id", "parent_event_id",
    "previous_event_id", "triggered_by_event_id", "started_event_id",
    "emission_sequence", "call_id",
}


def _set_event_attrs(span, event) -> None:
    """Push all non-internal event fields onto a span as llm.* attributes."""
    for key, value in event.model_dump().items():
        if key in _SKIP_FIELDS or value is None:
            continue
        attr_key = f"llm.{key}"
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(attr_key, value)
        else:
            span.set_attribute(attr_key, str(value))


class LLMOtelListener(BaseEventListener):
    """Subscribes to CrewAI's event bus and creates OTEL spans for LLM calls.

    CrewAI 0.186+ routes calls through provider-native SDKs (e.g. AnthropicCompletion)
    and bypasses litellm, so this event-based approach is the only reliable hook.
    Spans use Langfuse native OTEL attributes so token usage is tracked natively
    and consolidated automatically at the trace level.
    """

    def setup_listeners(self, bus):
        _tracer = otel_trace.get_tracer("crewai.llm")
        _active_spans: dict = {}

        def _event_key(event) -> str:
            call_id = getattr(event, "call_id", None)
            if call_id:
                return call_id
            return f"{event.source_fingerprint}:{getattr(event, 'task_id', '')}"

        @bus.on(LLMCallStartedEvent)
        def on_llm_start(source, event: LLMCallStartedEvent):
            span = _tracer.start_span(f"llm.{event.model}", context=get_current())
            _set_event_attrs(span, event)
            span.set_attribute(_OBSERVATION_TYPE, "generation")
            span.set_attribute(_OBSERVATION_MODEL, event.model)
            if event.messages:
                span.set_attribute(_OBSERVATION_INPUT, json.dumps(event.messages, default=str))
            _active_spans[_event_key(event)] = span

        @bus.on(LLMCallCompletedEvent)
        def on_llm_complete(source, event: LLMCallCompletedEvent):
            span = _active_spans.pop(_event_key(event), None)
            if span:
                _set_event_attrs(span, event)
                if event.response:
                    span.set_attribute(_OBSERVATION_OUTPUT, json.dumps(event.response, default=str))
                usage = getattr(event, "usage", None)
                if usage:
                    span.set_attribute(_OBSERVATION_USAGE, json.dumps(usage))
                span.end()

        @bus.on(LLMCallFailedEvent)
        def on_llm_fail(source, event: LLMCallFailedEvent):
            span = _active_spans.pop(_event_key(event), None)
            if span:
                _set_event_attrs(span, event)
                span.end()
