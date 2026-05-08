import sys
import os
import uuid
import warnings
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from employee_chatbot.crew import createCrew
from employee_chatbot.utils.memory import MemoryUtils
from deepeval.dataset import EvaluationDataset, Golden, ConversationalGolden
from utils.tool_tracker import ToolCallTracker

def generate_and_push_dataset():
    console = Console()
    console.print("[bold cyan]Starting Golden Dataset Generation...[/bold cyan]")
    
    # Define a list of test queries to bootstrap the golden dataset
    test_queries = [
        "What is the policy for earned leaves?",
        "How many leaves have I taken so far?",
        "I want to apply for 2 days of sick leave starting tomorrow."
    ]
    
    goldens = []
    
    for query in test_queries:
        console.print(f"\n[bold blue]Processing Query:[/bold blue] {query}")
        
        inputs = {
            'employee_query': query,
            'employee_id': str(uuid.uuid4()),
            'conversationHistory': "",
            'conversationSummary': ""
        }
        
        try:
            crew = createCrew()
            # ToolCallTracker records which tools the agent calls during this
            # run. Those names become the ground-truth expected_tools for this
            # golden, enabling trajectory evaluation in the test suite.
            with ToolCallTracker() as tracker:
                response = crew.kickoff(inputs=inputs).raw

            console.print(f"[bold green]Baseline Response Captured:[/bold green]\n{response}")
            console.print(f"[bold yellow]Tools called:[/bold yellow] {tracker.tool_names}")

            # Create a Golden object with expected_tools baked in
            golden = Golden(
                input=query,
                expected_output=response,
                expected_tools = tracker.tool_calls
            )
            goldens.append(golden)
            
        except Exception as e:
            console.print(f"[bold red]An error occurred generating golden for query '{query}': {e}[/bold red]")
            continue

    if not goldens:
        console.print("[bold red]No goldens were generated. Aborting push.[/bold red]")
        return

    # Create the Evaluation Dataset
    console.print("\n[bold cyan]Creating and pushing the EvaluationDataset to Confident AI...[/bold cyan]")
    try:
        dataset = EvaluationDataset(goldens=goldens)
        dataset.push(alias="Employee Chatbot Goldens")
        console.print("[bold green]Successfully pushed 'Employee Chatbot Goldens' dataset to Confident AI![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to push dataset to Confident AI: {e}[/bold red]")

def generate_and_push_multi_turn_dataset():
    goldens = [
        ConversationalGolden(
            scenario="Manpreet wants to go for a long vacation starting from the first working day of the coming month and wants to apply earned leave for the same. Manpreet's leave is already approved. This multi-turn interaction will be turn by turn. In the first turn, Manpreet wants to first check how many earned leaves are possible in a calendar year. And then in the second turn, Manpreet wants to check how many earned leaves he has taken in this calendar year. And then in the last turn Manpreet wants to apply for remaining possible earned leaves. While applying leaves, Manpreet wants to ignore Saturdays and Sundays before applying leaves. And hence multiple applications of earned leave might need to be submitted.",
            expected_outcome="Maximum earned leaves submitted into the system.",
            user_description="Manpreet is an employee of DeepLens."
        )
    ]
    # Create dataset and optionally push to Confident AI
    dataset = EvaluationDataset(goldens=goldens)
    dataset.push(alias="Employee Chatbot Multi Turn Goldens")

if __name__ == "__main__":
    generate_and_push_dataset()
    generate_and_push_multi_turn_dataset()
