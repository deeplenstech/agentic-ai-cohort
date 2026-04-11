#!/usr/bin/env python
import warnings
from dotenv import load_dotenv
from stockresearch.crew import crew
from langfuse import get_client
from openinference.instrumentation.crewai import CrewAIInstrumentor

load_dotenv()

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Step2: Setup langfuse for tracing
langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")
CrewAIInstrumentor().instrument(skip_dep_check=True)

def run():
    inputs = {
        'user_query': "Compare Google's current stock price to last month's price."
    }

    with langfuse.start_as_current_observation(name="stock-research", input=inputs):
        try:
            response = crew.kickoff(inputs=inputs).raw
            print(response)
            langfuse.update_current_span(output=response)
        except Exception as e:
            raise Exception(f"An error occurred while running the crew: {e}")
        finally:
            langfuse.flush()
