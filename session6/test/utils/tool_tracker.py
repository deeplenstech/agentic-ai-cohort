"""
ToolCallTracker
---------------
A context manager that listens to CrewAI's native ToolUsageFinishedEvent
and records every tool call made during a crew run.

Usage (in tests):
    with ToolCallTracker() as tracker:
        crew.kickoff(inputs=inputs)
    print(tracker.tool_calls)           # list[ToolCall]
    print(tracker.tool_names)           # list[str]  — for additional_metadata

Usage (in golden generation):
    with ToolCallTracker() as tracker:
        response = crew.kickoff(inputs=inputs).raw
    golden = Golden(
        input=query,
        expected_output=response,
        additional_metadata={"expected_tools": tracker.tool_names},
    )
"""

import re
from contextlib import contextmanager
from typing import Generator

from crewai.events.event_bus import crewai_event_bus
from crewai.events.types.tool_usage_events import ToolUsageFinishedEvent
from deepeval.test_case import ToolCall


def camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    s3 = re.sub(r"\s+", "_", s2)
    return re.sub(r"_+", "_", s3)


class ToolCallTracker:
    """
    Context manager that captures CrewAI tool call events and exposes them
    as DeepEval ``ToolCall`` objects.

    The listener is registered inside ``crewai_event_bus.scoped_handlers()``
    so it is automatically torn down when the ``with`` block exits, preventing
    handler accumulation across multiple parametrized test runs.
    """

    def __init__(self) -> None:
        self._tool_calls: list[ToolCall] = []
        self._scope_ctx = None  # holds the scoped_handlers context

    # ── Context manager protocol ──────────────────────────────────────────────

    def __enter__(self) -> "ToolCallTracker":
        self._tool_calls = []
        self._scope_ctx = crewai_event_bus.scoped_handlers()
        self._scope_ctx.__enter__()

        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def _on_tool_finished(source, event: ToolUsageFinishedEvent) -> None:
            # tool_args may arrive as a dict or a raw JSON string
            input_params = (
                event.tool_args
                if isinstance(event.tool_args, dict)
                else {"raw": event.tool_args}
            )
            self._tool_calls.append(
                ToolCall(
                    name=camel_to_snake(event.tool_name),
                    # input_parameters=input_params,
                    # output=str(event.output),
                )
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._scope_ctx is not None:
            self._scope_ctx.__exit__(exc_type, exc_val, exc_tb)
            self._scope_ctx = None

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def tool_calls(self) -> list[ToolCall]:
        """All ``ToolCall`` objects recorded during the run."""
        return list(self._tool_calls)

    @property
    def tool_names(self) -> list[str]:
        """
        Ordered list of tool names called during the run.
        Suitable for storing as ``additional_metadata["expected_tools"]``
        in a golden so that future test runs can verify tool trajectory.
        """
        return [tc.name for tc in self._tool_calls]
