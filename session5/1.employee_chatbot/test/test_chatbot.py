import sys
import os
import uuid
import pytest
from dotenv import load_dotenv

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

load_dotenv()

from deepeval.metrics import AnswerRelevancyMetric, GEval, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams, ToolCall
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset
from employee_chatbot.crew import createCrew

from test.utils.tool_tracker import ToolCallTracker

# 1. Pull the golden dataset from Confident AI
try:
    dataset = EvaluationDataset()
    dataset.pull(alias="Employee Chatbot Goldens")
except Exception as e:
    print(f"Failed to pull dataset: {e}")
    # Fallback to an empty list so pytest doesn't crash during collection
    dataset = EvaluationDataset(goldens=[])

# 2. Define the metrics to evaluate
answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.5)

correctness_metric = GEval(
    name="Correctness",
    criteria="Determine whether the actual output accurately conveys the same information and intent as the expected output, answering the user's query.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    threshold=0.5
)

# ToolCorrectnessMetric checks that the agent called the right tools
# (matched against expected_tools stored in each golden's additional_metadata).
tool_correctness_metric = ToolCorrectnessMetric(threshold=0.9, should_consider_ordering=True)

# print(dataset.goldens)

# 3. Parametrize the test function to run for every golden in the dataset
@pytest.mark.parametrize("golden", dataset.goldens)
def test_employee_chatbot_response(golden):
    # print (golden)

    # ── Trajectory capture via CrewAI event bus ───────────────────────────
    # ToolCallTracker subscribes to ToolUsageFinishedEvent for the duration
    # of the with-block, then tears down automatically — no handler leakage.
    with ToolCallTracker() as tracker:
        crew = createCrew()

        inputs = {
            'employee_query': golden.input,
            'employee_id': str(uuid.uuid4()),  # mock employee ID per run
            'conversationHistory': '',
            'conversationSummary': ''
        }

        # Execute the crew — ToolUsageFinishedEvent fires for every tool call
        actual_output = crew.kickoff(inputs=inputs).raw

        # ── Assemble DeepEval test case ───────────────────────────────────────
        test_case = LLMTestCase(
            input=golden.input,
            actual_output=actual_output,
            expected_output=golden.expected_output,
            tools_called=tracker.tool_calls,
            expected_tools=golden.expected_tools,
        )

        metrics = [answer_relevancy_metric, correctness_metric, tool_correctness_metric]
        
        assert_test(test_case, metrics)
