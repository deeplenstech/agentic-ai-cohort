import sys
import os
import uuid
import pytest
from dotenv import load_dotenv

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

load_dotenv()

from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset
from employee_chatbot.crew import createCrew

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

# 3. Parametrize the test function to run for every golden in the dataset
@pytest.mark.parametrize("golden", dataset.goldens)
def test_employee_chatbot_response(golden):
    crew = createCrew()
    
    # Construct the input payload
    inputs = {
        'employee_query': golden.input,
        'employee_id': str(uuid.uuid4()), # Short UUID as mock employee ID
        'conversationHistory': '', # Simplified history for stateless testing
        'userPreferences': ''
    }
    
    # Execute the crew to get the live response (actual output)
    actual_output = crew.kickoff(inputs=inputs).raw
    
    # Construct the DeepEval test case.
    # retrieval_context is NOT set here manually — it is captured automatically
    # by the @observe(type="retriever") decorator on retrieve_from_kb() in tools.py.
    # When the agent calls the KB tool, DeepEval traces the span and links
    # the retrieved chunks to this test case via the active trace context.
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        expected_output=golden.expected_output,
    )
    
    # 4. Assert the test case against the defined metrics
    assert_test(test_case, [answer_relevancy_metric, correctness_metric])
