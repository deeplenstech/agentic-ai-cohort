from crewai.events import LLMCallCompletedEvent, crewai_event_bus
from deepeval.integrations.crewai import handler
from deepeval.tracing.tracing import trace_manager
from deepeval.tracing.types import LlmSpan

def _capture_usage_handler(source, event: LLMCallCompletedEvent):
    """
    Surgically extracts token usage and applies it to the correct LLM span.
    
    Instead of relying on thread-local context (which is unreliable in CrewAI's 
    async event bus), this uses DeepEval's internal span mapping to find 
    the exact span instance for this specific LLM call.
    """
    # handler._listener_instance is the singleton that DeepEval uses to track spans
    if handler._listener_instance and hasattr(event, 'usage') and event.usage:
        # Generate the unique key DeepEval uses to track this LLM call
        key = handler._listener_instance.get_llm_execution_id(source, event)
        # Retrieve the observer (which holds the span UUID)
        observer = handler._listener_instance.span_observers.get(key)
        
        if observer:
            # Find the actual span object in deepeval's global trace manager
            span = trace_manager.get_span_by_uuid(observer.uuid)
            if span and isinstance(span, LlmSpan):
                # Extract usage (handling both Bedrock and standard LiteLLM keys)
                input_tokens = event.usage.get('inputTokens', event.usage.get('prompt_tokens'))
                output_tokens = event.usage.get('outputTokens', event.usage.get('completion_tokens'))
                
                if input_tokens is not None:
                    span.input_token_count = float(input_tokens)
                if output_tokens is not None:
                    span.output_token_count = float(output_tokens)

def apply_deepeval_patch():
    """Registers a surgical listener to capture token usage from CrewAI events."""
    # Register our handler to the global event bus.
    # It will run alongside deepeval's own handlers.
    crewai_event_bus.on(LLMCallCompletedEvent)(_capture_usage_handler)
    print("DeepEval CrewAI token usage listener registered surgically.")
