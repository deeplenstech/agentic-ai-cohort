import sys
import os
import uuid
from typing import List
from dotenv import load_dotenv
import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, ConversationalGolden
from deepeval.test_case import Turn
from deepeval.simulator import ConversationSimulator
from deepeval.metrics import TurnRelevancyMetric, ConversationCompletenessMetric

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

load_dotenv()

from employee_chatbot.crew import createCrew
from employee_chatbot.utils.memory import MemoryUtils

dataset = EvaluationDataset()
dataset.pull(alias="Employee Chatbot Multi Turn Goldens")

session_id = str(uuid.uuid4())
employee_id = str(uuid.uuid4())

# Wrap your chatbot in a callback func
def model_callback(input, turns: List[Turn], thread_id: str) -> Turn:
        # 1. Get latest simulated user input
        user_input = turns[-1].content
       
        # 2. Call chatbot
        memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)

        conversationHistory = memoryUtils.loadShortTermMemory(5)
        conversationSummary = memoryUtils.extractSummary()

        inputs = {
            'employee_query': user_input,
            'employee_id': employee_id,
            'conversationHistory': conversationHistory,
            'conversationSummary': conversationSummary
        }

        crew = createCrew()
        response = crew.kickoff(inputs=inputs).raw
        memoryUtils.saveMemory(userPrompt=user_input, assistantResponse=response)

        # 3. Return chatbot turn
        return Turn(role="assistant", content=response)
        
simulator = ConversationSimulator(model_callback=model_callback)
test_cases = simulator.simulate(conversational_goldens=dataset.goldens)

relevancy = TurnRelevancyMetric()
conversationCompleteness = ConversationCompletenessMetric()

@pytest.mark.parametrize("test_case", test_cases)
def test_multi_turn(test_case):
    assert_test(test_case, [relevancy, conversationCompleteness])